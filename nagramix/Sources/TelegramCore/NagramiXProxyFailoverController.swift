import Foundation
import SwiftSignalKit
import MtProtoKit

private enum NagramiXNetworkSettingsBridge {
    static let changedNotification = Notification.Name("NagramiXSettingsChanged")
    private static let autoSwitchEnabledKey = "nagramix.network.proxyAutoSwitchEnabled"
    private static let autoSwitchTimeoutKey = "nagramix.network.proxyAutoSwitchTimeout"

    static var proxyAutoSwitchEnabled: Bool {
        return UserDefaults.standard.object(forKey: self.autoSwitchEnabledKey) as? Bool ?? false
    }

    static var proxyAutoSwitchTimeout: Int {
        let value = UserDefaults.standard.integer(forKey: self.autoSwitchTimeoutKey)
        return [15, 30, 60].contains(value) ? value : 15
    }
}

final class NagramiXProxyFailoverController {
    private static let sharedQueue = Queue(name: "org.nagramix.proxy-failover")
    private static weak var failoverOwner: NagramiXProxyFailoverController?

    private let queue = NagramiXProxyFailoverController.sharedQueue
    private var accountManager: AccountManager<TelegramAccountManagerTypes>?
    private var network: Network?
    private var settingsDisposable: Disposable?
    private var statusDisposable: Disposable?
    private var probeDisposable: MTDisposable?
    private var settingsObserver: NSObjectProtocol?
    private var failureTimer: SwiftSignalKit.Timer?
    private var candidateTimer: SwiftSignalKit.Timer?
    private var proxySettings: ProxySettings = .defaultSettings
    private var connectionStatus: ConnectionStatus = .waitingForNetwork
    private var generation: Int = 0
    private var expectedActiveServer: ProxyServerSettings?
    private var suppressedFailureServer: ProxyServerSettings?
    private var remainingCandidates: [ProxyServerSettings] = []

    init() {
    }

    func start(accountManager: AccountManager<TelegramAccountManagerTypes>, network: Network) {
        self.queue.async { [weak self] in
            guard let self else {
                return
            }
            self.stopInternal()
            self.accountManager = accountManager
            self.network = network

            self.settingsDisposable = (accountManager.sharedData(keys: [SharedDataKeys.proxySettings])
            |> deliverOn(self.queue)).start(next: { [weak self] sharedData in
                guard let self else {
                    return
                }
                let settings = sharedData.entries[SharedDataKeys.proxySettings]?.get(ProxySettings.self) ?? .defaultSettings
                self.updateProxySettings(settings)
            })
            self.statusDisposable = (network.connectionStatus
            |> deliverOn(self.queue)).start(next: { [weak self] status in
                self?.updateConnectionStatus(status)
            })
            self.settingsObserver = NotificationCenter.default.addObserver(forName: NagramiXNetworkSettingsBridge.changedNotification, object: nil, queue: nil, using: { [weak self] _ in
                self?.queue.async {
                    self?.reevaluate()
                }
            })
        }
    }

    func stop() {
        self.queue.async { [weak self] in
            self?.stopInternal()
        }
    }

    private func stopInternal() {
        self.cancelFailureProcess(incrementGeneration: true)
        self.settingsDisposable?.dispose()
        self.settingsDisposable = nil
        self.statusDisposable?.dispose()
        self.statusDisposable = nil
        if let settingsObserver = self.settingsObserver {
            NotificationCenter.default.removeObserver(settingsObserver)
            self.settingsObserver = nil
        }
    }

    private func updateProxySettings(_ settings: ProxySettings) {
        let previousActiveServer = self.proxySettings.activeServer
        self.proxySettings = settings
        if previousActiveServer != settings.activeServer {
            if self.expectedActiveServer == settings.activeServer {
                // Keep the expected marker until the new connection is either
                // confirmed online or its confirmation timeout expires.
            } else {
                self.suppressedFailureServer = nil
                self.cancelFailureProcess(incrementGeneration: true)
            }
        }
        self.reevaluate()
    }

    private func updateConnectionStatus(_ status: ConnectionStatus) {
        self.connectionStatus = status
        switch status {
        case .online:
            self.suppressedFailureServer = nil
            self.cancelFailureProcess(incrementGeneration: true)
        case let .connecting(_, proxyHasConnectionIssues):
            if !proxyHasConnectionIssues {
                self.suppressedFailureServer = nil
                self.cancelFailureProcess(incrementGeneration: true)
            }
        case .waitingForNetwork, .updating:
            self.suppressedFailureServer = nil
            self.cancelFailureProcess(incrementGeneration: true)
        }
        self.reevaluate()
    }

    private func reevaluate() {
        guard NagramiXNetworkSettingsBridge.proxyAutoSwitchEnabled else {
            self.cancelFailureProcess(incrementGeneration: true)
            return
        }
        guard self.proxySettings.enabled, let activeServer = self.proxySettings.activeServer else {
            self.cancelFailureProcess(incrementGeneration: true)
            return
        }
        let uniqueServers = self.uniqueServers(self.proxySettings.servers)
        guard uniqueServers.count > 1 else {
            self.cancelFailureProcess(incrementGeneration: false)
            return
        }
        guard case let .connecting(_, proxyHasConnectionIssues) = self.connectionStatus, proxyHasConnectionIssues else {
            return
        }
        guard self.suppressedFailureServer != activeServer else {
            return
        }
        guard self.expectedActiveServer == nil else {
            return
        }
        guard self.failureTimer == nil, self.probeDisposable == nil, self.candidateTimer == nil else {
            return
        }
        guard NagramiXProxyFailoverController.failoverOwner == nil || NagramiXProxyFailoverController.failoverOwner === self else {
            return
        }
        NagramiXProxyFailoverController.failoverOwner = self

        let timeout = NagramiXNetworkSettingsBridge.proxyAutoSwitchTimeout
        let generation = self.generation
        let timer = SwiftSignalKit.Timer(timeout: Double(timeout), repeat: false, completion: { [weak self] in
            guard let self, generation == self.generation else {
                return
            }
            self.failureTimer = nil
            guard case let .connecting(_, stillFailing) = self.connectionStatus, stillFailing, self.proxySettings.activeServer == activeServer else {
                return
            }
            self.beginFailover(from: activeServer, servers: uniqueServers, generation: generation)
        }, queue: self.queue)
        self.failureTimer = timer
        timer.start()
    }

    private func beginFailover(from activeServer: ProxyServerSettings, servers: [ProxyServerSettings], generation: Int) {
        guard let currentIndex = servers.firstIndex(of: activeServer) else {
            self.suppressedFailureServer = activeServer
            return
        }
        let after = Array(servers[(currentIndex + 1)...])
        let before = currentIndex > 0 ? Array(servers[..<currentIndex]) : []
        self.remainingCandidates = after + before
        self.probeNextCandidate(generation: generation)
    }

    private func probeNextCandidate(generation: Int) {
        guard generation == self.generation, let network = self.network else {
            return
        }
        self.expectedActiveServer = nil
        guard !self.remainingCandidates.isEmpty else {
            self.suppressedFailureServer = self.proxySettings.activeServer
            self.cancelFailureProcess(incrementGeneration: false)
            return
        }
        let candidate = self.remainingCandidates.removeFirst()
        self.probeDisposable?.dispose()
        let probeTimeout = SwiftSignalKit.Timer(timeout: 12.0, repeat: false, completion: { [weak self] in
            guard let self, generation == self.generation else {
                return
            }
            self.candidateTimer = nil
            self.probeDisposable?.dispose()
            self.probeDisposable = nil
            self.probeNextCandidate(generation: generation)
        }, queue: self.queue)
        self.candidateTimer = probeTimeout
        probeTimeout.start()
        self.probeDisposable = MTProxyConnectivity.pingProxy(with: network.context, datacenterId: network.datacenterId, settings: candidate.mtProxySettings).start(next: { [weak self] value in
            guard let self else {
                return
            }
            self.queue.async {
                guard generation == self.generation else {
                    return
                }
                self.candidateTimer?.invalidate()
                self.candidateTimer = nil
                self.probeDisposable?.dispose()
                self.probeDisposable = nil
                guard let status = value as? MTProxyConnectivityStatus, status.reachable else {
                    self.probeNextCandidate(generation: generation)
                    return
                }
                self.applyCandidate(candidate, generation: generation)
            }
        })
    }

    private func applyCandidate(_ candidate: ProxyServerSettings, generation: Int) {
        guard generation == self.generation, let accountManager = self.accountManager else {
            return
        }
        self.expectedActiveServer = candidate
        let _ = (updateProxySettingsInteractively(accountManager: accountManager, { current in
            var current = current
            current.enabled = true
            current.activeServer = candidate
            return current
        })
        |> deliverOn(self.queue)).start(next: { [weak self] changed in
            guard let self, generation == self.generation else {
                return
            }
            if !changed && self.proxySettings.activeServer != candidate {
                self.expectedActiveServer = nil
                self.probeNextCandidate(generation: generation)
                return
            }
            let timer = SwiftSignalKit.Timer(timeout: 12.0, repeat: false, completion: { [weak self] in
                guard let self, generation == self.generation else {
                    return
                }
                self.candidateTimer = nil
                if case .online = self.connectionStatus, self.proxySettings.activeServer == candidate {
                    self.remainingCandidates.removeAll()
                    return
                }
                self.probeNextCandidate(generation: generation)
            }, queue: self.queue)
            self.candidateTimer = timer
            timer.start()
        })
    }

    private func uniqueServers(_ servers: [ProxyServerSettings]) -> [ProxyServerSettings] {
        var result: [ProxyServerSettings] = []
        var seen = Set<ProxyServerSettings>()
        for server in servers where seen.insert(server).inserted {
            result.append(server)
        }
        return result
    }

    private func cancelFailureTimerOnly() {
        self.failureTimer?.invalidate()
        self.failureTimer = nil
    }

    private func cancelFailureProcess(incrementGeneration: Bool) {
        if incrementGeneration {
            self.generation &+= 1
        }
        self.cancelFailureTimerOnly()
        self.candidateTimer?.invalidate()
        self.candidateTimer = nil
        self.probeDisposable?.dispose()
        self.probeDisposable = nil
        self.expectedActiveServer = nil
        self.remainingCandidates.removeAll()
        if NagramiXProxyFailoverController.failoverOwner === self {
            NagramiXProxyFailoverController.failoverOwner = nil
        }
    }
}
