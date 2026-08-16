#!/usr/bin/env python3
"""Apply the isolated NagramiX 0.1.9 feature overlay."""

from __future__ import annotations

import shutil
from pathlib import Path


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Pinned 0.1.9 patch anchor was not found ({label}): {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_between(path: Path, start: str, end: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    start_index = text.find(start)
    end_index = text.find(end, start_index + len(start))
    if start_index < 0 or end_index < 0:
        raise SystemExit(f"Pinned 0.1.9 patch range was not found ({label}): {path}")
    path.write_text(text[:start_index] + new + text[end_index:], encoding="utf-8")


def apply_features(source: Path) -> None:
    overlay = Path(__file__).resolve().parent

    core_source = overlay / "Sources" / "NagramiXCore"
    core_target = source / "submodules" / "NagramiXCore"
    if core_target.exists():
        raise SystemExit(f"NagramiXCore already exists in the source tree: {core_target}")
    shutil.copytree(core_source, core_target)

    mtproto_source = overlay / "Sources" / "MtProtoKit"
    mtproto_target = source / "submodules" / "MtProtoKit" / "Sources"
    shutil.copy2(mtproto_source / "NagramiXDNSResolver.h", mtproto_target / "NagramiXDNSResolver.h")
    shutil.copy2(mtproto_source / "NagramiXDNSResolver.m", mtproto_target / "NagramiXDNSResolver.m")
    mtproto_public = source / "submodules" / "MtProtoKit" / "PublicHeaders" / "MtProtoKit"
    shutil.copy2(mtproto_source / "NagramiXDNSResolver.h", mtproto_public / "NagramiXDNSResolver.h")
    replace_once(
        mtproto_public / "MtProtoKit.h",
        "#import <MtProtoKit/MTProxyConnectivity.h>\n",
        "#import <MtProtoKit/MTProxyConnectivity.h>\n#import <MtProtoKit/NagramiXDNSResolver.h>\n",
        "Expose NagramiX DoH endpoint validation to SettingsUI",
    )

    mt_dns = mtproto_target / "MTDNS.m"
    replace_once(
        mt_dns,
        '#import "MTDNS.h"\n',
        '#import "MTDNS.h"\n#import "NagramiXDNSResolver.h"\n',
        "NagramiX real DoH resolver import",
    )
    replace_once(
        mt_dns,
        """+ (MTSignal *)resolveHostnameUniversal:(NSString *)hostname port:(int32_t)port {
    return [[self resolveHostname:hostname] timeout:10.0 onQueue:[MTQueue concurrentDefaultQueue] orSignal:[self resolveHostnameNative:hostname port:port]];
}
""",
        """+ (MTSignal *)resolveHostnameUniversal:(NSString *)hostname port:(int32_t)port {
    if ([NagramiXDNSResolver usesSystemResolver]) {
        return [self resolveHostnameNative:hostname port:port];
    }
    return [[NagramiXDNSResolver resolveHostname:hostname] timeout:12.0 onQueue:[MTQueue concurrentDefaultQueue] orSignal:[MTSignal fail:nil]];
}

+ (MTSignal *)testDohEndpoint:(NSString *)endpoint hostname:(NSString *)hostname {
    return [[NagramiXDNSResolver testEndpoint:endpoint hostname:hostname] timeout:12.0 onQueue:[MTQueue concurrentDefaultQueue] orSignal:[MTSignal fail:nil]];
}
""",
        "Use selected System or DoH resolver in the real MTProto proxy DNS path",
    )

    mt_dns_header = mtproto_target / "MTDNS.h"
    replace_once(
        mt_dns_header,
        "+ (MTSignal *)resolveHostnameUniversal:(NSString *)hostname port:(int32_t)port;\n",
        "+ (MTSignal *)resolveHostnameUniversal:(NSString *)hostname port:(int32_t)port;\n+ (MTSignal *)testDohEndpoint:(NSString *)endpoint hostname:(NSString *)hostname;\n",
        "Expose Custom DoH validation through the actual resolver",
    )

    mt_tcp_connection = mtproto_target / "MTTcpConnection.m"
    replace_once(
        mt_tcp_connection,
        """                }];
            } file:__FILE_NAME__ line:__LINE__]];
""",
        """                }];
            } error:^(id error) {
                (void)error;
                [[MTTcpConnection tcpQueue] dispatchOnQueue:^{
                    __strong MTTcpConnection *strongSelf = weakSelf;
                    if (strongSelf != nil) {
                        [strongSelf closeAndNotifyWithError:true];
                    }
                }];
            } completed:nil file:__FILE_NAME__ line:__LINE__]];
""",
        "Close MTProto connection when the selected DoH resolver fails",
    )

    network_source = source / "submodules" / "TelegramCore" / "Sources" / "Network" / "Network.swift"
    replace_once(
        network_source,
        """    public func dropConnectionStatus() {
        _connectionStatus.set(.single(.waitingForNetwork))
    }
""",
        """    public func dropConnectionStatus() {
        _connectionStatus.set(.single(.waitingForNetwork))
    }

    public func reconnectForNagramiXDnsChange() {
        self.mtProto.simulateDisconnection()
        self.dropConnectionStatus()
    }
""",
        "Reconnect MTProto after a runtime DNS resolver change",
    )

    account_source = source / "submodules" / "TelegramCore" / "Sources" / "Account" / "Account.swift"
    replace_once(
        account_source,
        """        }))

        if !supplementary {
            let mediaBox = postbox.mediaBox
""",
        """        }))

        let nagramiXDnsObserver = NotificationCenter.default.addObserver(forName: Notification.Name("NagramiXDnsSettingsChanged"), object: nil, queue: nil, using: { _ in
            network.reconnectForNagramiXDnsChange()
        })
        self.managedOperationsDisposable.add(ActionDisposable {
            NotificationCenter.default.removeObserver(nagramiXDnsObserver)
        })

        if !supplementary {
            let mediaBox = postbox.mediaBox
""",
        "Reconnect every account network when the selected resolver changes",
    )
    replace_once(
        account_source,
        """        self.managedOperationsDisposable.add(ActionDisposable {
            NotificationCenter.default.removeObserver(nagramiXDnsObserver)
        })

        if !supplementary {
""",
        """        self.managedOperationsDisposable.add(ActionDisposable {
            NotificationCenter.default.removeObserver(nagramiXDnsObserver)
        })

        if !supplementary {
            let nagramiXProxyFailoverController = NagramiXProxyFailoverController()
            nagramiXProxyFailoverController.start(accountManager: accountManager, network: network)
            self.managedOperationsDisposable.add(ActionDisposable {
                nagramiXProxyFailoverController.stop()
            })
        }

        if !supplementary {
""",
        "Start the process-wide proxy failover controller outside UI lifecycle",
    )

    settings_controller_source = overlay / "Sources" / "SettingsUI" / "NagramiXSettingsController.swift"
    settings_controller_target = source / "submodules" / "SettingsUI" / "Sources" / settings_controller_source.name
    shutil.copy2(settings_controller_source, settings_controller_target)
    shutil.copy2(overlay / "Sources" / "SettingsUI" / "NagramiXCustomDohController.swift", settings_controller_target.parent / "NagramiXCustomDohController.swift")

    telegram_core_overlay = overlay / "Sources" / "TelegramCore" / "NagramiXProxyFailoverController.swift"
    telegram_core_target = source / "submodules" / "TelegramCore" / "Sources" / "Network" / telegram_core_overlay.name
    shutil.copy2(telegram_core_overlay, telegram_core_target)

    settings_build = source / "submodules" / "SettingsUI" / "BUILD"
    replace_once(
        settings_build,
        '        "//submodules/AccountContext:AccountContext",\n',
        '        "//submodules/AccountContext:AccountContext",\n        "//submodules/NagramiXCore:NagramiXCore",\n',
        "SettingsUI NagramiXCore dependency",
    )

    proxy_list = source / "submodules" / "SettingsUI" / "Sources" / "Data and Storage" / "ProxyListSettingsController.swift"
    replace_once(
        proxy_list,
        "import UrlEscaping\n",
        "import UrlEscaping\nimport NagramiXCore\n",
        "Proxy settings NagramiXCore import",
    )
    replace_between(
        proxy_list,
        "private final class ProxySettingsControllerArguments {",
        "private struct ProxySettingsControllerState: Equatable {",
        (overlay / "Sources" / "SettingsUI" / "ProxyListNagramiXBlock.swift.inc").read_text(encoding="utf-8"),
        "Proxy screen DNS and automatic failover controls",
    )
    replace_once(
        proxy_list,
        """    var pushControllerImpl: ((ViewController) -> Void)?
    var dismissImpl: (() -> Void)?
""",
        """    var pushControllerImpl: ((ViewController) -> Void)?
    var presentControllerImpl: ((ViewController) -> Void)?
    var dismissImpl: (() -> Void)?
""",
        "Proxy settings presentation callback",
    )
    replace_once(
        proxy_list,
        "    var shareProxyListImpl: (() -> Void)?\n    \n    let arguments = ProxySettingsControllerArguments(toggleEnabled: { value in\n",
        """    var shareProxyListImpl: (() -> Void)?
    let nagramiXSettingsPromise = ValuePromise(NagramiXTabSettings.current, ignoreRepeated: false)
    let updateNagramiXSettings: ((inout NagramiXTabSettings) -> Void) -> Void = { transform in
        NagramiXTabSettings.update(transform)
        nagramiXSettingsPromise.set(NagramiXTabSettings.current)
    }
    var selectDnsImpl: (() -> Void)?
    var editCustomDohImpl: (() -> Void)?
    var selectTimeoutImpl: (() -> Void)?

    let arguments = ProxySettingsControllerArguments(toggleEnabled: { value in
""",
        "Proxy settings persistent NagramiX state",
    )
    replace_once(
        proxy_list,
        """        }).start()
    }, addNewServer: {
""",
        """        }).start()
    }, selectDns: {
        selectDnsImpl?()
    }, editCustomDoh: {
        editCustomDohImpl?()
    }, toggleAutoSwitch: { value in
        updateNagramiXSettings { $0.proxyAutoSwitchEnabled = value }
    }, selectAutoSwitchTimeout: {
        selectTimeoutImpl?()
    }, addNewServer: {
""",
        "Proxy settings DNS and Auto-Switch actions",
    )
    replace_once(
        proxy_list,
        """    let proxySettings = Promise<ProxySettings>()
""",
        """    editCustomDohImpl = {
        guard let context else {
            return
        }
        let current = NagramiXTabSettings.current
        presentControllerImpl?(nagramiXCustomDohController(context: context, initialValue: current.customDohUrl, apply: { value in
            updateNagramiXSettings {
                $0.customDohUrl = value
                $0.dnsProvider = .customDoh
            }
        }, clear: {
            updateNagramiXSettings {
                $0.customDohUrl = ""
                $0.dnsProvider = .system
            }
        }))
    }
    selectDnsImpl = {
        let presentationData = sharedContext.currentPresentationData.with { $0 }
        let actionSheet = ActionSheetController(presentationData: presentationData)
        let current = NagramiXTabSettings.current
        let providers: [NagramiXDnsProvider] = [.system, .google, .quad9, .adGuard, .mullvad, .cloudflare, .customDoh]
        let items: [ActionSheetItem] = providers.map { provider in
            ActionSheetButtonItem(title: (current.dnsProvider == provider ? "✓ " : "") + nagramiXDnsTitle(provider, strings: presentationData.strings), color: .accent, action: { [weak actionSheet] in
                actionSheet?.dismissAnimated()
                if provider == .customDoh && current.customDohUrl.isEmpty {
                    editCustomDohImpl?()
                } else {
                    updateNagramiXSettings { $0.dnsProvider = provider }
                }
            })
        }
        var providerItems: [ActionSheetItem] = [ActionSheetTextItem(title: presentationData.strings.nagramiXDns)]
        providerItems.append(contentsOf: items)
        actionSheet.setItemGroups([
            ActionSheetItemGroup(items: providerItems),
            ActionSheetItemGroup(items: [ActionSheetButtonItem(title: presentationData.strings.Common_Cancel, color: .accent, font: .bold, action: { [weak actionSheet] in actionSheet?.dismissAnimated() })])
        ])
        presentControllerImpl?(actionSheet)
    }
    selectTimeoutImpl = {
        let presentationData = sharedContext.currentPresentationData.with { $0 }
        let actionSheet = ActionSheetController(presentationData: presentationData)
        let currentTimeout = NagramiXTabSettings.current.proxyAutoSwitchTimeout
        let values = [15, 30, 60]
        let items: [ActionSheetItem] = values.map { value in
            ActionSheetButtonItem(title: (currentTimeout == value ? "✓ " : "") + nagramiXTimeoutTitle(value, strings: presentationData.strings), color: .accent, action: { [weak actionSheet] in
                actionSheet?.dismissAnimated()
                updateNagramiXSettings { $0.proxyAutoSwitchTimeout = value }
            })
        }
        var timeoutItems: [ActionSheetItem] = [ActionSheetTextItem(title: presentationData.strings.nagramiXProxySwitchAfter)]
        timeoutItems.append(contentsOf: items)
        actionSheet.setItemGroups([
            ActionSheetItemGroup(items: timeoutItems),
            ActionSheetItemGroup(items: [ActionSheetButtonItem(title: presentationData.strings.Common_Cancel, color: .accent, font: .bold, action: { [weak actionSheet] in actionSheet?.dismissAnimated() })])
        ])
        presentControllerImpl?(actionSheet)
    }

    let proxySettings = Promise<ProxySettings>()
""",
        "Native DNS and Auto-Switch selectors plus Custom DoH editor",
    )
    replace_once(
        proxy_list,
        """    let signal = combineLatest(updatedPresentationData, statePromise.get(), proxySettings.get(), statusesContext.statuses(), network.connectionStatus)
    |> map { presentationData, state, proxySettings, statuses, connectionStatus -> (ItemListControllerState, (ItemListNodeState, Any)) in
""",
        """    let signal = combineLatest(updatedPresentationData, statePromise.get(), proxySettings.get(), statusesContext.statuses(), network.connectionStatus, nagramiXSettingsPromise.get())
    |> map { presentationData, state, proxySettings, statuses, connectionStatus, nagramiXSettings -> (ItemListControllerState, (ItemListNodeState, Any)) in
""",
        "Observe NagramiX networking settings in Proxy screen",
    )
    replace_once(
        proxy_list,
        "entries: proxySettingsControllerEntries(theme: presentationData.theme, strings: presentationData.strings, state: state, proxySettings: proxySettings, statuses: statuses, connectionStatus: connectionStatus)",
        "entries: proxySettingsControllerEntries(theme: presentationData.theme, strings: presentationData.strings, state: state, proxySettings: proxySettings, nagramiXSettings: nagramiXSettings, statuses: statuses, connectionStatus: connectionStatus)",
        "Render NagramiX networking settings",
    )
    replace_once(
        proxy_list,
        """    pushControllerImpl = { [weak controller] c in
        (controller?.navigationController as? NavigationController)?.pushViewController(c)
    }
""",
        """    pushControllerImpl = { [weak controller] c in
        (controller?.navigationController as? NavigationController)?.pushViewController(c)
    }
    presentControllerImpl = { [weak controller] c in
        controller?.present(c, in: .window(.root))
    }
""",
        "Present Proxy selectors and Custom DoH editor",
    )

    telegram_ui_build = source / "submodules" / "TelegramUI" / "BUILD"
    replace_once(
        telegram_ui_build,
        '        "//submodules/SettingsUI:SettingsUI",\n',
        '        "//submodules/SettingsUI:SettingsUI",\n        "//submodules/NagramiXCore:NagramiXCore",\n',
        "TelegramUI NagramiXCore dependency",
    )

    tab_bar_build = source / "submodules" / "TabBarUI" / "BUILD"
    replace_once(
        tab_bar_build,
        '        "//submodules/Display",\n',
        '        "//submodules/Display",\n        "//submodules/NagramiXCore:NagramiXCore",\n',
        "TabBarUI NagramiXCore dependency",
    )

    chat_list_build = source / "submodules" / "ChatListUI" / "BUILD"
    replace_once(
        chat_list_build,
        '        "//submodules/AccountContext:AccountContext",\n',
        '        "//submodules/AccountContext:AccountContext",\n        "//submodules/NagramiXCore:NagramiXCore",\n',
        "ChatListUI NagramiXCore dependency",
    )

    video_message_build = source / "submodules" / "TelegramUI" / "Components" / "VideoMessageCameraScreen" / "BUILD"
    replace_once(
        video_message_build,
        '        "//submodules/AccountContext",\n',
        '        "//submodules/AccountContext",\n        "//submodules/NagramiXCore:NagramiXCore",\n',
        "VideoMessageCameraScreen NagramiXCore dependency",
    )

    story_container_build = source / "submodules" / "TelegramUI" / "Components" / "Stories" / "StoryContainerScreen" / "BUILD"
    replace_once(
        story_container_build,
        '        "//submodules/AccountContext",\n',
        '        "//submodules/AccountContext",\n        "//submodules/NagramiXCore:NagramiXCore",\n',
        "StoryContainerScreen NagramiXCore dependency",
    )

    settings_items = source / "submodules" / "TelegramUI" / "Components" / "PeerInfo" / "PeerInfoScreen" / "Sources" / "PeerInfoSettingsItems.swift"
    replace_once(
        settings_items,
        "import TelegramPresentationData\n",
        "import TelegramPresentationData\nimport NagramiXCore\n",
        "NagramiX settings localization import",
    )
    replace_once(
        settings_items,
        "    case myProfile\n    case proxy\n",
        "    case nagramix\n    case myProfile\n    case proxy\n",
        "NagramiX settings group order",
    )
    replace_once(
        settings_items,
        """        items[.myProfile]!.append(PeerInfoScreenDisclosureItem(id: 0, text: presentationData.strings.Settings_MyProfile, icon: PresentationResourcesSettings.myProfile, action: {
            interaction.openSettings(.profile)
        }))
""" + "        \n" + """        if !settings.proxySettings.servers.isEmpty {
""",
        """        items[.nagramix]!.append(PeerInfoScreenDisclosureItem(id: 0, text: presentationData.strings.nagramiXSettingsTitle, icon: PresentationResourcesSettings.appearance, action: {
            interaction.openSettings(.nagramix)
        }))

        items[.myProfile]!.append(PeerInfoScreenDisclosureItem(id: 0, text: presentationData.strings.Settings_MyProfile, icon: PresentationResourcesSettings.myProfile, action: {
            interaction.openSettings(.profile)
        }))
""" + "        \n" + """        if !settings.proxySettings.servers.isEmpty {
""",
        "NagramiX settings row",
    )

    peer_info_screen = source / "submodules" / "TelegramUI" / "Components" / "PeerInfo" / "PeerInfoScreen" / "Sources" / "PeerInfoScreen.swift"
    replace_once(
        peer_info_screen,
        "    case profile\n    case premiumManagement\n",
        "    case profile\n    case nagramix\n    case premiumManagement\n",
        "NagramiX settings route",
    )

    settings_actions = source / "submodules" / "TelegramUI" / "Components" / "PeerInfo" / "PeerInfoScreen" / "Sources" / "PeerInfoScreenSettingsActions.swift"
    replace_once(
        settings_actions,
        """        case .stories:
            push(PeerInfoStoryGridScreen(context: self.context, peerId: self.context.account.peerId, scope: .saved))
""",
        """        case .nagramix:
            push(nagramiXSettingsController(context: self.context))
        case .stories:
            push(PeerInfoStoryGridScreen(context: self.context, peerId: self.context.account.peerId, scope: .saved))
""",
        "NagramiX settings navigation",
    )

    root_controller = source / "submodules" / "TelegramUI" / "Sources" / "TelegramRootController.swift"
    replace_once(
        root_controller,
        "import SettingsUI\n",
        "import SettingsUI\nimport NagramiXCore\n",
        "Telegram root NagramiXCore import",
    )
    replace_once(
        root_controller,
        """    private var applicationInFocusDisposable: Disposable?
    private var storyUploadEventsDisposable: Disposable?
""",
        """    private var applicationInFocusDisposable: Disposable?
    private var storyUploadEventsDisposable: Disposable?
    private var nagramiXTabSettingsObserver: NSObjectProtocol?
    private var nagramiXTabInterfaceSoftRestartObserver: NSObjectProtocol?
    private var nagramiXOriginalTabTitles: [ObjectIdentifier: String] = [:]
""",
        "Telegram root tab settings state",
    )
    replace_once(
        root_controller,
        """        super.init(mode: .automaticMasterDetail, theme: NavigationControllerTheme(presentationTheme: self.presentationData.theme))
""" + "        \n" + """        self.presentationDataDisposable = (context.sharedContext.presentationData
""",
        """        super.init(mode: .automaticMasterDetail, theme: NavigationControllerTheme(presentationTheme: self.presentationData.theme))

        self.nagramiXTabSettingsObserver = NotificationCenter.default.addObserver(forName: NagramiXTabSettings.changedNotification, object: nil, queue: .main, using: { [weak self] _ in
            self?.applyNagramiXTabSettings()
        })
        self.nagramiXTabInterfaceSoftRestartObserver = NotificationCenter.default.addObserver(forName: NagramiXTabSettings.softRestartRequestedNotification, object: nil, queue: .main, using: { [weak self] _ in
            self?.softRestartNagramiXTabInterface()
        })
""" + "        \n" + """        self.presentationDataDisposable = (context.sharedContext.presentationData
""",
        "Telegram root tab settings observer",
    )
    replace_once(
        root_controller,
        """        self.storyUploadEventsDisposable?.dispose()
    }
""",
        """        self.storyUploadEventsDisposable?.dispose()
        if let nagramiXTabSettingsObserver = self.nagramiXTabSettingsObserver {
            NotificationCenter.default.removeObserver(nagramiXTabSettingsObserver)
        }
        if let nagramiXTabInterfaceSoftRestartObserver = self.nagramiXTabInterfaceSoftRestartObserver {
            NotificationCenter.default.removeObserver(nagramiXTabInterfaceSoftRestartObserver)
        }
    }
""",
        "Telegram root observer cleanup",
    )
    replace_once(
        root_controller,
        """    public func addRootControllers(showCallsTab: Bool) {
""",
        """    private func nagramiXConfiguredControllers() -> [ViewController] {
        let settings = NagramiXTabSettings.current
        let possibleControllers: [ViewController?] = [self.contactsController, self.callListController, self.chatListController, self.accountSettingsController]
        let allControllers: [ViewController] = possibleControllers.compactMap { $0 }

        for controller in allControllers {
            let identifier = ObjectIdentifier(controller)
            if self.nagramiXOriginalTabTitles[identifier] == nil, let title = controller.tabBarItem.title {
                self.nagramiXOriginalTabTitles[identifier] = title
            }
            controller.tabBarItem.title = settings.hideTitles ? "" : self.nagramiXOriginalTabTitles[identifier]
        }

        var controllers: [ViewController] = []
        if !settings.hideContacts, let contactsController = self.contactsController {
            controllers.append(contactsController)
        }
        if !settings.hideCalls, let callListController = self.callListController {
            controllers.append(callListController)
        }
        if let chatListController = self.chatListController {
            controllers.append(chatListController)
        }
        if let accountSettingsController = self.accountSettingsController {
            controllers.append(accountSettingsController)
        }
        return controllers
    }

    private func applyNagramiXTabSettings() {
        guard let rootTabController = self.rootTabController as? TabBarControllerImpl else {
            return
        }
        rootTabController.setControllers(self.nagramiXConfiguredControllers(), selectedIndex: nil)
        rootTabController.updateLayout(transition: .immediate)
    }

    private func softRestartNagramiXTabInterface() {
        guard let previousTabController = self.rootTabController as? TabBarControllerImpl else {
            return
        }

        var navigationControllers = self.viewControllers
        guard let rootIndex = navigationControllers.firstIndex(where: { $0 === previousTabController }) else {
            return
        }

        let selectedController: ViewController?
        if previousTabController.selectedIndex >= 0 && previousTabController.selectedIndex < previousTabController.controllers.count {
            selectedController = previousTabController.controllers[previousTabController.selectedIndex]
        } else {
            selectedController = nil
        }

        let tabBarController = TabBarControllerImpl(theme: self.presentationData.theme, strings: self.presentationData.strings)
        tabBarController.navigationPresentation = .master
        self.rootTabController = tabBarController

        let controllers = self.nagramiXConfiguredControllers()
        let selectedIndex = selectedController.flatMap { selectedController in
            controllers.firstIndex(where: { $0 === selectedController })
        } ?? controllers.firstIndex(where: { $0 === self.accountSettingsController }) ?? 0
        previousTabController.setControllers([], selectedIndex: nil)
        tabBarController.setControllers(controllers, selectedIndex: selectedIndex)

        navigationControllers[rootIndex] = tabBarController
        self.setViewControllers(navigationControllers, animated: false)
        tabBarController.updateLayout(transition: .immediate)
    }

    public func addRootControllers(showCallsTab: Bool) {
""",
        "Telegram root tab settings helpers",
    )
    replace_once(
        root_controller,
        """        var controllers: [ViewController] = []
""" + "        \n" + """        let contactsController = ContactsController(context: self.context)
""",
        """        let contactsController = ContactsController(context: self.context)
""",
        "Telegram root temporary controllers array",
    )
    replace_once(root_controller, "        controllers.append(contactsController)\n        \n", "", "Telegram root contacts default append")
    replace_once(
        root_controller,
        """        if showCallsTab {
            controllers.append(callListController)
        }
        controllers.append(chatListController)
""" + "        \n",
        "",
        "Telegram root calls and chats default append",
    )
    replace_once(
        root_controller,
        """        accountSettingsController.parentController = self
        controllers.append(accountSettingsController)
""" + "                \n" + """        tabBarController.setControllers(controllers, selectedIndex: restoreSettignsController != nil ? (controllers.count - 1) : (controllers.count - 2))
""" + "        \n" + """        self.contactsController = contactsController
        self.callListController = callListController
        self.chatListController = chatListController
        self.accountSettingsController = accountSettingsController
        self.rootTabController = tabBarController
""",
        """        accountSettingsController.parentController = self

        self.contactsController = contactsController
        self.callListController = callListController
        self.chatListController = chatListController
        self.accountSettingsController = accountSettingsController
        self.rootTabController = tabBarController

        let controllers = self.nagramiXConfiguredControllers()
        let selectedController: ViewController = restoreSettignsController != nil ? accountSettingsController : chatListController
        let selectedIndex = controllers.firstIndex(where: { $0 === selectedController }) ?? 0
        tabBarController.setControllers(controllers, selectedIndex: selectedIndex)
""",
        "Telegram root initial NagramiX tabs",
    )
    replace_once(
        root_controller,
        """    public func updateRootControllers(showCallsTab: Bool) {
        guard let rootTabController = self.rootTabController as? TabBarControllerImpl else {
            return
        }
        var controllers: [ViewController] = []
        controllers.append(self.contactsController!)
        if showCallsTab {
            controllers.append(self.callListController!)
        }
        controllers.append(self.chatListController!)
        controllers.append(self.accountSettingsController!)
""" + "        \n" + """        rootTabController.setControllers(controllers, selectedIndex: nil)
    }
""",
        """    public func updateRootControllers(showCallsTab: Bool) {
        self.applyNagramiXTabSettings()
    }
""",
        "Telegram root updates",
    )

    tab_bar_node = source / "submodules" / "TabBarUI" / "Sources" / "TabBarContollerNode.swift"
    replace_once(
        tab_bar_node,
        "import GlassControls\n",
        "import GlassControls\nimport NagramiXCore\n",
        "Tab bar NagramiXCore import",
    )
    replace_once(
        tab_bar_node,
        """                search: self.currentController?.tabBarSearchState.flatMap { tabBarSearchState in
                    return TabBarComponent.Search(
""",
        """                search: self.currentController?.tabBarSearchState.flatMap { tabBarSearchState in
                    guard NagramiXTabSettings.current.showSearchButton else {
                        return nil
                    }
                    return TabBarComponent.Search(
""",
        "Tab bar search visibility",
    )

    video_message_camera = source / "submodules" / "TelegramUI" / "Components" / "VideoMessageCameraScreen" / "Sources" / "VideoMessageCameraScreen.swift"
    replace_once(
        video_message_camera,
        "import AccountContext\n",
        "import AccountContext\nimport AVFoundation\nimport NagramiXCore\n",
        "Video message camera NagramiXCore import",
    )
    replace_once(
        video_message_camera,
        '            let isFrontPosition = "".isEmpty\n',
        """            let prefersRearCamera = NagramiXTabSettings.current.useRearCameraForVideoMessages
            let hasRearCamera = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back) != nil
            let isFrontPosition = !prefersRearCamera || !hasRearCamera
""",
        "Video messages start on the configured camera",
    )

    camera_source = source / "submodules" / "Camera" / "Sources" / "Camera.swift"
    replace_once(
        camera_source,
        """        if self.initialConfiguration.isRoundVideo {
            return mainDeviceContext.output.startRecording(mode: .roundVideo, orientation: DeviceModel.current.isIpad ? orientation : .portrait, additionalOutput: self.additionalDeviceContext?.output)
""",
        """        if self.initialConfiguration.isRoundVideo {
            // In dual-camera mode CameraOutput defaults to the front stream.
            // Synchronize it with the position shown in the preview before the
            // recorder starts, so the sent round video uses the same camera.
            mainDeviceContext.output.markPositionChange(position: self.positionValue)
            return mainDeviceContext.output.startRecording(mode: .roundVideo, orientation: DeviceModel.current.isIpad ? orientation : .portrait, additionalOutput: self.additionalDeviceContext?.output)
""",
        "Record round video from the camera selected in the preview",
    )

    chat_list_controller = source / "submodules" / "ChatListUI" / "Sources" / "ChatListController.swift"
    replace_once(
        chat_list_controller,
        "import TelegramPresentationData\n",
        "import TelegramPresentationData\nimport NagramiXCore\n",
        "Chat list NagramiXCore import",
    )
    replace_once(
        chat_list_controller,
        """        let hasProxy = context.sharedContext.accountManager.sharedData(keys: [SharedDataKeys.proxySettings])
        |> map { sharedData -> (Bool, Bool) in
            if let settings = sharedData.entries[SharedDataKeys.proxySettings]?.get(ProxySettings.self) {
                return (!settings.servers.isEmpty, settings.enabled)
            } else {
                return (false, false)
            }
        }
        |> distinctUntilChanged(isEqual: { lhs, rhs in
            return lhs == rhs
        })
""",
        """        let showProxyButton = Signal<Bool, NoError> { subscriber in
            subscriber.putNext(NagramiXTabSettings.current.showProxyButton)
            let observer = NotificationCenter.default.addObserver(forName: NagramiXTabSettings.changedNotification, object: nil, queue: nil, using: { _ in
                subscriber.putNext(NagramiXTabSettings.current.showProxyButton)
            })
            return ActionDisposable {
                NotificationCenter.default.removeObserver(observer)
            }
        }
        |> distinctUntilChanged
        let hasProxy = combineLatest(context.sharedContext.accountManager.sharedData(keys: [SharedDataKeys.proxySettings]), showProxyButton)
        |> map { sharedData, showProxyButton -> (Bool, Bool) in
            let settings = sharedData.entries[SharedDataKeys.proxySettings]?.get(ProxySettings.self) ?? .defaultSettings
            return (showProxyButton, settings.enabled)
        }
        |> distinctUntilChanged(isEqual: { lhs, rhs in
            return lhs == rhs
        })
""",
        "Keep the Chat proxy button visible independently from saved proxies",
    )
    replace_once(
        chat_list_controller,
        """                        self.leftButton = AnyComponentWithIdentity(id: "edit", component: AnyComponent(NavigationButtonComponent(
                            content: .text(title: presentationData.strings.Common_Edit, isBold: false),
""",
        """                        self.leftButton = AnyComponentWithIdentity(id: "edit", component: AnyComponent(NavigationButtonComponent(
                            content: .text(title: presentationData.strings.nagramiXEdit, isBold: false),
""",
        "Use the full localized Edit title on the root Chat screen",
    )
    replace_once(
        chat_list_controller,
        "    private var displayedStoriesTooltip: Bool = false\n",
        "    private var displayedStoriesTooltip: Bool = false\n    private var nagramiXSettingsObserver: NSObjectProtocol?\n    private var nagramiXLastOrderedStorySubscriptions: EngineStorySubscriptions?\n",
        "Chat list NagramiX settings observer state",
    )
    replace_once(
        chat_list_controller,
        "    public var hasStorySubscriptions: Bool {\n        if let rawStorySubscriptions = self.rawStorySubscriptions, !rawStorySubscriptions.items.isEmpty {\n",
        "    public var hasStorySubscriptions: Bool {\n        if NagramiXTabSettings.current.hideStories {\n            return false\n        }\n        if let rawStorySubscriptions = self.rawStorySubscriptions, !rawStorySubscriptions.items.isEmpty {\n",
        "Hidden stories do not report a visible subscription feed",
    )
    replace_once(
        chat_list_controller,
        "        super.init(context: context, navigationBarPresentationData: nil)\n        \n        self.accessoryPanelContainer = ASDisplayNode()\n",
        """        super.init(context: context, navigationBarPresentationData: nil)

        self.nagramiXSettingsObserver = NotificationCenter.default.addObserver(forName: NagramiXTabSettings.changedNotification, object: nil, queue: .main, using: { [weak self] _ in
            guard let self else {
                return
            }
            self.orderedStorySubscriptions = NagramiXTabSettings.current.hideStories ? nil : (self.nagramiXLastOrderedStorySubscriptions ?? self.rawStorySubscriptions)
            let transition: ContainedViewLayoutTransition = self.didAppear ? .animated(duration: 0.4, curve: .spring) : .immediate
            self.chatListDisplayNode.temporaryContentOffsetChangeTransition = transition
            self.requestLayout(transition: transition)
            self.chatListDisplayNode.temporaryContentOffsetChangeTransition = nil
            if NagramiXTabSettings.current.hideStories {
                self.chatListDisplayNode.scrollToTopIfStoriesAreExpanded()
            }
        })

        self.accessoryPanelContainer = ASDisplayNode()
""",
        "Observe immediate story visibility changes",
    )
    replace_once(
        chat_list_controller,
        "        self.globalControlPanelsContextStateDisposable?.dispose()\n    }\n",
        """        self.globalControlPanelsContextStateDisposable?.dispose()
        if let nagramiXSettingsObserver = self.nagramiXSettingsObserver {
            NotificationCenter.default.removeObserver(nagramiXSettingsObserver)
        }
    }
""",
        "Chat list observer cleanup",
    )
    replace_once(
        chat_list_controller,
        """                    self.orderedStorySubscriptions = EngineStorySubscriptions(
                        accountItem: rawStorySubscriptions.accountItem,
                        items: items,
                        hasMoreToken: rawStorySubscriptions.hasMoreToken
                    )
""",
        """                    let orderedStorySubscriptions = EngineStorySubscriptions(
                        accountItem: rawStorySubscriptions.accountItem,
                        items: items,
                        hasMoreToken: rawStorySubscriptions.hasMoreToken
                    )
                    self.nagramiXLastOrderedStorySubscriptions = orderedStorySubscriptions
                    self.orderedStorySubscriptions = NagramiXTabSettings.current.hideStories ? nil : orderedStorySubscriptions
""",
        "Hide the chat-list story feed without removing story data",
    )
    replace_once(
        chat_list_controller,
        "    func storyCameraPanGestureChanged(transitionFraction: CGFloat) {\n        guard let rootController = self.context.sharedContext.mainWindow?.viewController as? TelegramRootControllerInterface else {\n",
        "    func storyCameraPanGestureChanged(transitionFraction: CGFloat) {\n        if NagramiXTabSettings.current.disableStoryCameraSwipe && self.storyCameraTransitionInCoordinator == nil {\n            return\n        }\n        guard let rootController = self.context.sharedContext.mainWindow?.viewController as? TelegramRootControllerInterface else {\n",
        "Disable only the story-camera swipe gesture",
    )
    replace_once(
        chat_list_controller,
        """            componentView.storyComposeAction = { [weak self] offset in
                guard let self else {
                    return
                }
                self.openStoryCamera(fromList: true, gesturePullOffset: offset)
            }
""",
        """            componentView.storyComposeAction = { [weak self] offset in
                guard let self else {
                    return
                }
                guard !NagramiXTabSettings.current.disableStoryCameraSwipe else {
                    return
                }
                self.openStoryCamera(fromList: true, gesturePullOffset: offset)
            }
""",
        "Disable the story-carousel pull gesture without disabling explicit camera buttons",
    )

    story_container_screen = source / "submodules" / "TelegramUI" / "Components" / "Stories" / "StoryContainerScreen" / "Sources" / "StoryContainerScreen.swift"
    replace_once(
        story_container_screen,
        "import TelegramCore\n",
        "import TelegramCore\nimport TelegramPresentationData\nimport NagramiXCore\n",
        "Story viewer NagramiX imports",
    )
    replace_once(
        story_container_screen,
        """    private let context: AccountContext
    private var didAnimateIn: Bool = false
    private var isDismissed: Bool = false
""",
        """    private let context: AccountContext
    private static var nagramiXConfirmationParentIds = Set<ObjectIdentifier>()
    private var didAnimateIn: Bool = false
    private var isDismissed: Bool = false
    private let nagramiXContent: StoryContentContext
    private weak var nagramiXTransitionSourceView: UIView?
    private var nagramiXPresentationDisposable: Disposable?
    private var nagramiXSettingsObserver: NSObjectProtocol?
""",
        "Story presentation and settings state",
    )
    replace_once(
        story_container_screen,
        """    ) {
        self.context = context
""" + "        \n" + """        super.init(context: context, component: StoryContainerScreenComponent(
            context: context,
            content: content,
""",
        """    ) {
        self.context = context
        self.nagramiXContent = content
        self.nagramiXTransitionSourceView = transitionIn?.sourceView

        super.init(context: context, component: StoryContainerScreenComponent(
            context: context,
            content: content,
""",
        "Keep the real story context available while presentation is pending",
    )
    replace_once(
        story_container_screen,
        """        self.context.sharedContext.hasPreloadBlockingContent.set(.single(true))
    }
""",
        """        self.context.sharedContext.hasPreloadBlockingContent.set(.single(true))

        self.nagramiXSettingsObserver = NotificationCenter.default.addObserver(forName: NagramiXTabSettings.changedNotification, object: nil, queue: .main, using: { [weak self] _ in
            self?.requestLayout(forceUpdate: true, transition: .immediate)
        })
    }
""",
        "Refresh built-in story actions immediately when NagramiX settings change",
    )
    replace_once(
        story_container_screen,
        """    deinit {
        self.context.sharedContext.hasPreloadBlockingContent.set(.single(false))
        self.focusedItemPromise.set(.single(nil))
    }
""",
        """    deinit {
        self.nagramiXPresentationDisposable?.dispose()
        if let nagramiXSettingsObserver = self.nagramiXSettingsObserver {
            NotificationCenter.default.removeObserver(nagramiXSettingsObserver)
        }
        self.context.sharedContext.hasPreloadBlockingContent.set(.single(false))
        self.focusedItemPromise.set(.single(nil))
    }
""",
        "Clean up story presentation and settings observers",
    )
    replace_once(
        story_container_screen,
        """    override public func containerLayoutUpdated(_ layout: ContainerViewLayout, transition: ContainedViewLayoutTransition) {
        super.containerLayoutUpdated(layout, transition: transition)
    }
""",
        """    override public func containerLayoutUpdated(_ layout: ContainerViewLayout, transition: ContainedViewLayoutTransition) {
        super.containerLayoutUpdated(layout, transition: transition)
    }

    public func nagramiXPresent(from parentController: ViewController, action: @escaping () -> Void) {
        guard NagramiXTabSettings.current.confirmStoryViewing else {
            action()
            return
        }

        let presentForState: (StoryContentContextState) -> Void = { [weak self, weak parentController] state in
            guard let self, let parentController else {
                return
            }
            guard let slice = state.slice else {
                self.nagramiXTransitionSourceView?.isHidden = false
                return
            }
            if slice.effectivePeer.id == self.context.account.peerId {
                action()
                return
            }

            let parentId = ObjectIdentifier(parentController)
            if StoryContainerScreen.nagramiXConfirmationParentIds.contains(parentId) {
                self.nagramiXTransitionSourceView?.isHidden = false
                return
            }
            StoryContainerScreen.nagramiXConfirmationParentIds.insert(parentId)

            let presentationData = self.context.sharedContext.currentPresentationData.with { $0 }
            let actionSheet = ActionSheetController(presentationData: presentationData)
            var didAccept = false
            actionSheet.dismissed = { [weak self] _ in
                StoryContainerScreen.nagramiXConfirmationParentIds.remove(parentId)
                if !didAccept {
                    self?.nagramiXTransitionSourceView?.isHidden = false
                }
            }
            actionSheet.setItemGroups([
                ActionSheetItemGroup(items: [
                    ActionSheetTextItem(title: presentationData.strings.nagramiXStoryConfirmationTitle + "\\n" + presentationData.strings.nagramiXStoryConfirmationText),
                    ActionSheetButtonItem(title: presentationData.strings.nagramiXViewStoryAction, color: .accent, font: .bold, action: { [weak actionSheet] in
                        didAccept = true
                        StoryContainerScreen.nagramiXConfirmationParentIds.remove(parentId)
                        actionSheet?.dismissAnimated()
                        action()
                    }),
                ]),
                ActionSheetItemGroup(items: [
                    ActionSheetButtonItem(title: presentationData.strings.Common_Cancel, color: .accent, font: .bold, action: { [weak actionSheet] in
                        actionSheet?.dismissAnimated()
                    }),
                ]),
            ])
            parentController.present(actionSheet, in: .window(.root))
        }

        if let state = self.nagramiXContent.stateValue {
            presentForState(state)
        } else {
            self.nagramiXPresentationDisposable = (self.nagramiXContent.state
            |> take(1)
            |> deliverOnMainQueue).start(next: { state in
                presentForState(state)
            })
        }
    }

    public func nagramiXPush(from parentController: ViewController, completion: @escaping () -> Void = {}) {
        self.nagramiXPresent(from: parentController, action: { [weak self, weak parentController] in
            guard let self, let parentController else {
                return
            }
            parentController.push(self)
            completion()
        })
    }

    public func nagramiXPush(from navigationController: NavigationController, completion: @escaping () -> Void = {}) {
        self.nagramiXPresent(from: navigationController, action: { [weak self, weak navigationController] in
            guard let self, let navigationController else {
                return
            }
            navigationController.pushViewController(self)
            completion()
        })
    }
""",
        "Confirm an external story before it is pushed onto the navigation stack",
    )

    replace_once(
        chat_list_controller,
        "            self.push(storyContainerScreen)\n",
        "            storyContainerScreen.nagramiXPush(from: self)\n",
        "Confirm chat-list stories before pushing the viewer",
    )

    message_stats_controller = source / "submodules" / "StatisticsUI" / "Sources" / "MessageStatsController.swift"
    replace_once(
        message_stats_controller,
        "            controller.push(storyContainerScreen)\n",
        "            storyContainerScreen.nagramiXPush(from: controller)\n",
        "Confirm message-stat stories before pushing the viewer",
    )

    channel_stats_controller = source / "submodules" / "StatisticsUI" / "Sources" / "ChannelStatsController.swift"
    replace_once(
        channel_stats_controller,
        "            controller.push(storyContainerScreen)\n",
        "            storyContainerScreen.nagramiXPush(from: controller)\n",
        "Confirm channel-stat stories before pushing the viewer",
    )

    open_resolved_url = source / "submodules" / "TelegramUI" / "Sources" / "OpenResolvedUrl.swift"
    replace_once(
        open_resolved_url,
        "                        navigationController?.pushViewController(storyContainerScreen)\n",
        "                        if let navigationController {\n                            storyContainerScreen.nagramiXPush(from: navigationController)\n                        }\n",
        "Confirm deep-linked stories before pushing the viewer",
    )

    open_chat_message = source / "submodules" / "TelegramUI" / "Sources" / "OpenChatMessage.swift"
    replace_once(
        open_chat_message,
        "            navigationController?.pushViewController(storyContainerScreen)\n",
        "            if let navigationController {\n                storyContainerScreen.nagramiXPush(from: navigationController)\n            }\n",
        "Confirm message-linked stories before pushing the viewer",
    )

    chat_controller = source / "submodules" / "TelegramUI" / "Sources" / "ChatController.swift"
    replace_once(
        chat_controller,
        "                self.push(storyContainerScreen)\n",
        "                storyContainerScreen.nagramiXPush(from: self)\n",
        "Confirm in-chat stories before pushing the viewer",
    )

    open_stories = source / "submodules" / "TelegramUI" / "Components" / "Stories" / "StoryContainerScreen" / "Sources" / "OpenStories.swift"
    replace_once(
        open_stories,
        "            parentController?.push(storyContainerScreen)\n",
        "            if let parentController {\n                storyContainerScreen.nagramiXPush(from: parentController)\n            }\n",
        "Confirm archived stories before pushing the viewer",
    )
    replace_once(
        open_stories,
        "            parentController?.push(storyContainerScreen)\n            completion(storyContainerScreen)\n",
        "            if let parentController {\n                storyContainerScreen.nagramiXPush(from: parentController, completion: {\n                    completion(storyContainerScreen)\n                })\n            }\n",
        "Confirm peer stories before pushing the viewer",
    )

    story_item_set_component = source / "submodules" / "TelegramUI" / "Components" / "Stories" / "StoryContainerScreen" / "Sources" / "StoryItemSetContainerComponent.swift"
    replace_once(
        story_item_set_component,
        "                controller.push(storyContainerScreen)\n",
        "                storyContainerScreen.nagramiXPush(from: controller)\n",
        "Confirm repost-chain stories before pushing the viewer",
    )

    peer_info_story_pane = source / "submodules" / "TelegramUI" / "Components" / "PeerInfo" / "PeerInfoVisualMediaPaneNode" / "Sources" / "PeerInfoStoryPaneNode.swift"
    replace_once(
        peer_info_story_pane,
        "                navigationController.pushViewController(storyContainerScreen)\n",
        "                storyContainerScreen.nagramiXPush(from: navigationController)\n",
        "Confirm media-pane stories before pushing the viewer",
    )

    peer_info_open_stories = source / "submodules" / "TelegramUI" / "Components" / "PeerInfo" / "PeerInfoScreen" / "Sources" / "PeerInfoScreenOpenStories.swift"
    replace_once(
        peer_info_open_stories,
        "                self.controller?.push(storyContainerScreen)\n",
        "                if let controller = self.controller {\n                    storyContainerScreen.nagramiXPush(from: controller)\n                }\n",
        "Confirm profile-header stories before pushing the viewer",
    )

    peer_info_screen = source / "submodules" / "TelegramUI" / "Components" / "PeerInfo" / "PeerInfoScreen" / "Sources" / "PeerInfoScreen.swift"
    replace_once(
        peer_info_screen,
        "                self.controller?.push(storyContainerScreen)\n",
        "                if let controller = self.controller {\n                    storyContainerScreen.nagramiXPush(from: controller)\n                }\n",
        "Confirm profile stories before pushing the viewer",
    )

    story_footer_panel = source / "submodules" / "TelegramUI" / "Components" / "Stories" / "StoryFooterPanelComponent" / "Sources" / "StoryFooterPanelComponent.swift"
    replace_once(
        story_footer_panel,
        "    public let canShare: Bool\n    public let externalViews: EngineStoryItem.Views?\n",
        "    public let canShare: Bool\n    public let canRepost: Bool\n    public let externalViews: EngineStoryItem.Views?\n",
        "Story footer repost capability state",
    )
    replace_once(
        story_footer_panel,
        "        canShare: Bool,\n        externalViews: EngineStoryItem.Views?,\n",
        "        canShare: Bool,\n        canRepost: Bool,\n        externalViews: EngineStoryItem.Views?,\n",
        "Story footer repost capability argument",
    )
    replace_once(
        story_footer_panel,
        "        self.canShare = canShare\n        self.externalViews = externalViews\n",
        "        self.canShare = canShare\n        self.canRepost = canRepost\n        self.externalViews = externalViews\n",
        "Story footer repost capability assignment",
    )
    replace_once(
        story_footer_panel,
        "        if lhs.externalViews != rhs.externalViews {\n",
        "        if lhs.canRepost != rhs.canRepost {\n            return false\n        }\n        if lhs.externalViews != rhs.externalViews {\n",
        "Story footer repost capability equality",
    )
    replace_once(
        story_footer_panel,
        """                    let repostButton: ComponentView<Empty>
                    if let current = self.repostButton {
                        repostButton = current
                    } else {
                        repostButton = ComponentView()
                        self.repostButton = repostButton
                    }
""" + "                    \n" + """                    let forwardButton: ComponentView<Empty>
""",
        """                    let forwardButton: ComponentView<Empty>
""",
        "Create a repost button only when NagramiX enables it",
    )
    replace_once(
        story_footer_panel,
        """                    let repostButtonSize = repostButton.update(
                        transition: likeStatsTransition,
                        component: AnyComponent(MessageInputActionButtonComponent(
                            mode: .repost,
                            storyId: component.storyItem.id,
                            action: { [weak self] _, action, _ in
                                guard let self, let component = self.component else {
                                    return
                                }
                                guard case .up = action else {
                                    return
                                }
                                component.repostAction()
                            },
                            longPressAction: nil,
                            switchMediaInputMode: {
                            },
                            updateMediaCancelFraction: { _ in
                            },
                            lockMediaRecording: {
                            },
                            stopAndPreviewMediaRecording: {
                            },
                            moreAction: { _, _ in },
                            context: component.context,
                            theme: component.theme,
                            strings: component.strings,
                            presentController: { _ in },
                            audioRecorder: nil,
                            videoRecordingStatus: nil
                        )),
                        environment: {},
                        containerSize: CGSize(width: 33.0, height: 33.0)
                    )
                    if let repostButtonView = repostButton.view as? MessageInputActionButtonComponent.View {
                        if repostButtonView.superview == nil {
                            self.addSubview(repostButtonView)
                        }
                        var repostButtonFrame = CGRect(origin: CGPoint(x: rightContentOffset - repostButtonSize.width, y: floor((size.height - repostButtonSize.height) * 0.5)), size: repostButtonSize)
                        repostButtonFrame.origin.y += component.expandFraction * 45.0
""" + "                        \n" + """                        forwardStatsTransition.setPosition(view: repostButtonView, position: repostButtonFrame.center)
                        forwardStatsTransition.setBounds(view: repostButtonView, bounds: CGRect(origin: CGPoint(), size: repostButtonFrame.size))
                        forwardStatsTransition.setAlpha(view: repostButtonView, alpha: 1.0 - component.expandFraction)
""" + "                        \n" + """                        rightContentOffset -= repostButtonSize.width + 14.0
""" + "                        \n" + """                        if forwardStatsText.superview == nil {
                            repostButtonView.button.view.addSubview(forwardStatsText)
                        }
""" + "                        \n" + """                        forwardStatsFrame.origin.x -= repostButtonFrame.minX
                        forwardStatsFrame.origin.y -= repostButtonFrame.minY
                        forwardStatsTransition.setPosition(view: forwardStatsText, position: forwardStatsFrame.center)
                        forwardStatsTransition.setBounds(view: forwardStatsText, bounds: CGRect(origin: CGPoint(), size: forwardStatsFrame.size))
                    }
""" + "                    \n",
        """                    if component.canRepost {
                        let repostButton: ComponentView<Empty>
                        if let current = self.repostButton {
                            repostButton = current
                        } else {
                            repostButton = ComponentView()
                            self.repostButton = repostButton
                        }

                        let repostButtonSize = repostButton.update(
                            transition: likeStatsTransition,
                            component: AnyComponent(MessageInputActionButtonComponent(
                                mode: .repost,
                                storyId: component.storyItem.id,
                                action: { [weak self] _, action, _ in
                                    guard let self, let component = self.component else {
                                        return
                                    }
                                    guard case .up = action else {
                                        return
                                    }
                                    component.repostAction()
                                },
                                longPressAction: nil,
                                switchMediaInputMode: {
                                },
                                updateMediaCancelFraction: { _ in
                                },
                                lockMediaRecording: {
                                },
                                stopAndPreviewMediaRecording: {
                                },
                                moreAction: { _, _ in },
                                context: component.context,
                                theme: component.theme,
                                strings: component.strings,
                                presentController: { _ in },
                                audioRecorder: nil,
                                videoRecordingStatus: nil
                            )),
                            environment: {},
                            containerSize: CGSize(width: 33.0, height: 33.0)
                        )
                        if let repostButtonView = repostButton.view as? MessageInputActionButtonComponent.View {
                            if repostButtonView.superview == nil {
                                self.addSubview(repostButtonView)
                            }
                            var repostButtonFrame = CGRect(origin: CGPoint(x: rightContentOffset - repostButtonSize.width, y: floor((size.height - repostButtonSize.height) * 0.5)), size: repostButtonSize)
                            repostButtonFrame.origin.y += component.expandFraction * 45.0

                            forwardStatsTransition.setPosition(view: repostButtonView, position: repostButtonFrame.center)
                            forwardStatsTransition.setBounds(view: repostButtonView, bounds: CGRect(origin: CGPoint(), size: repostButtonFrame.size))
                            forwardStatsTransition.setAlpha(view: repostButtonView, alpha: 1.0 - component.expandFraction)

                            rightContentOffset -= repostButtonSize.width + 14.0

                            if forwardStatsText.superview == nil {
                                repostButtonView.button.view.addSubview(forwardStatsText)
                            }

                            forwardStatsFrame.origin.x -= repostButtonFrame.minX
                            forwardStatsFrame.origin.y -= repostButtonFrame.minY
                            forwardStatsTransition.setPosition(view: forwardStatsText, position: forwardStatsFrame.center)
                            forwardStatsTransition.setBounds(view: forwardStatsText, bounds: CGRect(origin: CGPoint(), size: forwardStatsFrame.size))
                        }
                    } else if let repostButton = self.repostButton {
                        self.repostButton = nil
                        repostButton.view?.removeFromSuperview()
                    }

""",
        "Hide the built-in repost action while keeping forwarding available",
    )

    story_item_set_component = source / "submodules" / "TelegramUI" / "Components" / "Stories" / "StoryContainerScreen" / "Sources" / "StoryItemSetContainerComponent.swift"
    replace_once(
        story_item_set_component,
        "import TelegramCore\n",
        "import TelegramCore\nimport NagramiXCore\n",
        "Story footer NagramiXCore import",
    )
    replace_once(
        story_item_set_component,
        "                                    canShare: canShare,\n                                    externalViews: nil,\n",
        "                                    canShare: canShare,\n                                    canRepost: canShare && NagramiXTabSettings.current.enableStoryRepost,\n                                    externalViews: nil,\n",
        "Combine NagramiX repost preference with Telegram forwarding restrictions",
    )

    story_send_message = source / "submodules" / "TelegramUI" / "Components" / "Stories" / "StoryContainerScreen" / "Sources" / "StoryItemSetContainerViewSendMessage.swift"
    replace_once(
        story_send_message,
        "import TelegramCore\n",
        "import TelegramCore\nimport NagramiXCore\n",
        "Story share sheet NagramiXCore import",
    )
    replace_once(
        story_send_message,
        """            let shareController = component.context.sharedContext.makeShareController(context: component.context, params: ShareControllerParams(
""",
        """            let shareStory: (() -> Void)?
            if NagramiXTabSettings.current.enableStoryRepost {
                shareStory = { [weak view] in
                    guard let view else {
                        return
                    }
                    view.openStoryEditing(repost: true)
                }
            } else {
                shareStory = nil
            }

            let shareController = component.context.sharedContext.makeShareController(context: component.context, params: ShareControllerParams(
""",
        "Prepare the optional built-in repost-to-story action",
    )
    replace_once(
        story_send_message,
        """                shareStory: { [weak view] in
                    guard let view else {
                        return
                    }
                    view.openStoryEditing(repost: true)
                }
""",
        """                shareStory: shareStory
""",
        "Hide the share-sheet repost action when disabled",
    )

    message_share_menu = source / "submodules" / "TelegramUI" / "Sources" / "ChatControllerOpenMessageShareMenu.swift"
    replace_once(
        message_share_menu,
        "import TelegramCore\n",
        "import TelegramCore\nimport NagramiXCore\n",
        "Message share sheet NagramiXCore import",
    )
    replace_once(
        message_share_menu,
        "        let shareStory: (() -> Void)? = canShareToStory ? { [weak self] in\n",
        "        let shareStory: (() -> Void)? = (canShareToStory && NagramiXTabSettings.current.enableStoryRepost) ? { [weak self] in\n",
        "Gate the built-in public-message repost action with the NagramiX setting",
    )

    app_delegate = source / "submodules" / "TelegramUI" / "Sources" / "AppDelegate.swift"
    replace_once(
        app_delegate,
        """                var icons = [
                    PresentationAppIcon(name: "BlueIcon", imageName: "BlueIcon", isDefault: buildConfig.isAppStoreBuild),
                    PresentationAppIcon(name: "New2", imageName: "New2"),
                    PresentationAppIcon(name: "New1", imageName: "New1"),
                    PresentationAppIcon(name: "BlackIcon", imageName: "BlackIcon"),
                    PresentationAppIcon(name: "BlueClassicIcon", imageName: "BlueClassicIcon"),
                    PresentationAppIcon(name: "BlackClassicIcon", imageName: "BlackClassicIcon"),
                    PresentationAppIcon(name: "BlueFilledIcon", imageName: "BlueFilledIcon"),
                    PresentationAppIcon(name: "BlackFilledIcon", imageName: "BlackFilledIcon")
                ]
                if buildConfig.isInternalBuild {
                    icons.append(PresentationAppIcon(name: "WhiteFilledIcon", imageName: "WhiteFilledIcon"))
                }
""" + "                \n" + """                icons.append(PresentationAppIcon(name: "Premium", imageName: "Premium", isPremium: true))
                icons.append(PresentationAppIcon(name: "PremiumTurbo", imageName: "PremiumTurbo", isPremium: true))
                icons.append(PresentationAppIcon(name: "PremiumBlack", imageName: "PremiumBlack", isPremium: true))
""" + "                \n" + """                return icons
""",
        """                return [
                    PresentationAppIcon(name: "NagramiX1", imageName: "NagramiX1Preview", isDefault: true),
                    PresentationAppIcon(name: "NagramiX2", imageName: "NagramiX2"),
                    PresentationAppIcon(name: "NagramiX3", imageName: "NagramiX3"),
                    PresentationAppIcon(name: "NagramiX4", imageName: "NagramiX4"),
                    PresentationAppIcon(name: "NagramiX5", imageName: "NagramiX5"),
                    PresentationAppIcon(name: "NagramiX6", imageName: "NagramiX6"),
                    PresentationAppIcon(name: "NagramiX7", imageName: "NagramiX7"),
                    PresentationAppIcon(name: "NagramiX8", imageName: "NagramiX8")
                ]
""",
        "NagramiX app icon list",
    )

    icon_item = source / "submodules" / "SettingsUI" / "Sources" / "Themes" / "ThemeSettingsAppIconItem.swift"
    replace_once(
        icon_item,
        "import TelegramPresentationData\n",
        "import TelegramPresentationData\nimport NagramiXCore\n",
        "NagramiX app icon localization import",
    )
    replace_once(
        icon_item,
        """                                case "PremiumTurbo":
                                    name = item.strings.Appearance_AppIconTurbo
                                default:
""",
        """                                case "PremiumTurbo":
                                    name = item.strings.Appearance_AppIconTurbo
                                case "NagramiX1":
                                    name = item.strings.nagramiXIconMain
                                case "NagramiX2":
                                    name = item.strings.nagramiXIconSunset
                                case "NagramiX3":
                                    name = item.strings.nagramiXIconAurora
                                case "NagramiX4":
                                    name = item.strings.nagramiXIconGraphite
                                case "NagramiX5":
                                    name = item.strings.nagramiXIconAmber
                                case "NagramiX6":
                                    name = item.strings.nagramiXIconNeon
                                case "NagramiX7":
                                    name = item.strings.nagramiXIconLime
                                case "NagramiX8":
                                    name = item.strings.nagramiXIconRuby
                                default:
""",
        "NagramiX app icon display names",
    )

    telegram_build = source / "Telegram" / "BUILD"
    replace_once(
        telegram_build,
        """alternate_icon_folders = [
    "BlackIcon",
    "BlackClassicIcon",
    "BlackFilledIcon",
    "BlueIcon",
    "BlueClassicIcon",
    "BlueFilledIcon",
    "WhiteFilledIcon",
    "New1",
    "New2",
    "Premium",
    "PremiumBlack",
    "PremiumTurbo",
]
""",
        """alternate_icon_folders = [
    "NagramiX2",
    "NagramiX3",
    "NagramiX4",
    "NagramiX5",
    "NagramiX6",
    "NagramiX7",
    "NagramiX8",
]
""",
        "NagramiX alternate icon build targets",
    )

    replace_once(
        telegram_build,
        'composer_icon_folders = ["Telegram"]\n',
        'composer_icon_folders = []\n',
        "Disable the differently scaled Icon Composer primary icon",
    )
    replace_once(
        telegram_build,
        '    app_icons = [ ":{}_icon".format(name) for name in composer_icon_folders ],\n',
        '    app_icons = [":NagramiXPrimaryIcon"],\n',
        "Use the NagramiX1 appiconset as the primary icon",
    )
    replace_once(
        telegram_build,
        '''filegroup(
    name = "DefaultIcon",
    srcs = glob([
        "Telegram-iOS/AppIcons.xcassets/BlueIcon.appiconset/*.png",
    ]),
)
''',
        '''filegroup(
    name = "DefaultIcon",
    srcs = glob([
        "Telegram-iOS/AppIcons.xcassets/NagramiX1.appiconset/*.png",
    ]),
)

filegroup(
    name = "NagramiXPrimaryIcon",
    srcs = glob([
        "Telegram-iOS/AppIcons.xcassets/NagramiX1.appiconset/**/*",
    ]),
)
''',
        "Expose the NagramiX1 appiconset to rules_apple",
    )

    print("Applied isolated NagramiX 0.1.9 feature overlay")
