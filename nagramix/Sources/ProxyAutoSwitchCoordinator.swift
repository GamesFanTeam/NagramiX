import Foundation
import MtProtoKit
import Postbox
import SwiftSignalKit

/// One lifecycle-aware failover coordinator per Telegram account.
/// A healthy proxy is never rotated just because the interval elapsed.
final class ProxyAutoSwitchCoordinator: Disposable {
    private let queue = Queue(name: "NagramiX-ProxyAutoSwitch")
    private let accountManager: AccountManager<TelegramAccountManagerTypes>
    private let network: Network

    private var stateDisposable: Disposable?
    private var checkDisposable: Disposable?
    private var timer: SwiftSignalKit.Timer?
    private var settings: ProxySettings = .defaultSettings
    private var status: ConnectionStatus = .waitingForNetwork
    private var generation: Int = 0
    private var checking = false

    init(accountManager: AccountManager<TelegramAccountManagerTypes>, network: Network) {
        self.accountManager = accountManager
        self.network = network

        let proxySettings = accountManager.sharedData(keys: [SharedDataKeys.proxySettings])
        |> map { data -> ProxySettings in
            return data.entries[SharedDataKeys.proxySettings]?.get(ProxySettings.self) ?? .defaultSettings
        }

        self.stateDisposable = (combineLatest(proxySettings, network.connectionStatus)
        |> deliverOn(self.queue)).start(next: { [weak self] settings, status in
            self?.update(settings: settings, status: status)
        })
    }

    func dispose() {
        self.queue.async { [weak self] in
            guard let self else {
                return
            }
            self.generation += 1
            self.timer?.invalidate()
            self.timer = nil
            self.checkDisposable?.dispose()
            self.checkDisposable = nil
            self.stateDisposable?.dispose()
            self.stateDisposable = nil
            self.checking = false
        }
    }

    private func update(settings: ProxySettings, status: ConnectionStatus) {
        assert(self.queue.isCurrent())

        let configurationChanged = self.settings.autoSwitchEnabled != settings.autoSwitchEnabled
            || self.settings.autoSwitchInterval != settings.autoSwitchInterval
            || self.settings.enabled != settings.enabled
            || self.settings.activeServer != settings.activeServer
            || self.settings.servers != settings.servers

        self.settings = settings
        self.status = status

        if configurationChanged {
            self.generation += 1
            self.timer?.invalidate()
            self.timer = nil
            self.checkDisposable?.dispose()
            self.checkDisposable = nil
            self.checking = false
        }

        guard settings.autoSwitchEnabled, settings.enabled, settings.activeServer != nil, settings.servers.count > 1 else {
            self.cancelTimer()
            return
        }

        switch status {
        case .waitingForNetwork, .online, .updating:
            self.cancelTimer()
        case .connecting:
            if !self.checking && self.timer == nil {
                self.scheduleCheck(after: settings.validatedAutoSwitchInterval)
            }
        }
    }

    private func cancelTimer() {
        self.timer?.invalidate()
        self.timer = nil
    }

    private func scheduleCheck(after seconds: Double) {
        assert(self.queue.isCurrent())
        self.timer?.invalidate()
        let timer = SwiftSignalKit.Timer(timeout: seconds, repeat: false, completion: { [weak self] in
            guard let self else {
                return
            }
            self.timer = nil
            self.beginFailover()
        }, queue: self.queue)
        self.timer = timer
        timer.start()
    }

    private func beginFailover() {
        assert(self.queue.isCurrent())
        guard !self.checking,
              self.settings.autoSwitchEnabled,
              self.settings.enabled,
              let activeServer = self.settings.activeServer,
              self.settings.servers.count > 1 else {
            return
        }

        guard case .connecting = self.status else {
            return
        }

        let uniqueServers = self.settings.servers.reduce(into: [ProxyServerSettings]()) { result, server in
            if !result.contains(server) {
                result.append(server)
            }
        }
        guard uniqueServers.count > 1 else {
            return
        }

        let activeIndex = uniqueServers.firstIndex(of: activeServer) ?? 0
        let candidates = (1 ..< uniqueServers.count).map { offset in
            uniqueServers[(activeIndex + offset) % uniqueServers.count]
        }

        self.checking = true
        self.generation += 1
        self.checkCandidate(candidates, index: 0, generation: self.generation)
    }

    private func checkCandidate(_ candidates: [ProxyServerSettings], index: Int, generation: Int) {
        assert(self.queue.isCurrent())
        guard generation == self.generation, index < candidates.count else {
            self.checking = false
            if generation == self.generation, self.settings.autoSwitchEnabled, case .connecting = self.status {
                self.scheduleCheck(after: self.settings.validatedAutoSwitchInterval)
            }
            return
        }

        let candidate = candidates[index]
        let signal = Signal<Bool, NoError> { subscriber in
            let disposable = MTProxyConnectivity.pingProxy(
                with: self.network.context,
                datacenterId: self.network.datacenterId,
                settings: candidate.mtProxySettings
            ).start(next: { value in
                if let value = value as? MTProxyConnectivityStatus {
                    subscriber.putNext(value.reachable)
                    subscriber.putCompletion()
                }
            })
            return ActionDisposable {
                disposable?.dispose()
            }
        }
        |> runOn(self.queue)

        self.checkDisposable = signal.start(next: { [weak self] available in
            guard let self, generation == self.generation else {
                return
            }
            guard self.settings.servers.contains(candidate) else {
                self.checkCandidate(candidates, index: index + 1, generation: generation)
                return
            }
            if available {
                self.checking = false
                self.generation += 1
                let _ = updateProxySettingsInteractively(accountManager: self.accountManager, { current in
                    var current = current
                    guard current.autoSwitchEnabled, current.servers.contains(candidate) else {
                        return current
                    }
                    current.activeServer = candidate
                    current.enabled = true
                    return current
                }).start()
            } else {
                self.checkCandidate(candidates, index: index + 1, generation: generation)
            }
        })
    }
}
