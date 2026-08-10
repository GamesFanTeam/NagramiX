#!/usr/bin/env python3
"""Apply the isolated NagramiX 0.1.6 tabs and app-icon overlay."""

from __future__ import annotations

import shutil
from pathlib import Path


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Pinned 0.1.6 patch anchor was not found ({label}): {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def apply_features(source: Path) -> None:
    overlay = Path(__file__).resolve().parent

    core_source = overlay / "Sources" / "NagramiXCore"
    core_target = source / "submodules" / "NagramiXCore"
    if core_target.exists():
        raise SystemExit(f"NagramiXCore already exists in the source tree: {core_target}")
    shutil.copytree(core_source, core_target)

    settings_controller_source = overlay / "Sources" / "SettingsUI" / "NagramiXSettingsController.swift"
    settings_controller_target = source / "submodules" / "SettingsUI" / "Sources" / settings_controller_source.name
    shutil.copy2(settings_controller_source, settings_controller_target)

    settings_build = source / "submodules" / "SettingsUI" / "BUILD"
    replace_once(
        settings_build,
        '        "//submodules/AccountContext:AccountContext",\n',
        '        "//submodules/AccountContext:AccountContext",\n        "//submodules/NagramiXCore:NagramiXCore",\n',
        "SettingsUI NagramiXCore dependency",
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

    settings_items = source / "submodules" / "TelegramUI" / "Components" / "PeerInfo" / "PeerInfoScreen" / "Sources" / "PeerInfoSettingsItems.swift"
    replace_once(
        settings_items,
        "    case myProfile\n    case proxy\n",
        "    case myProfile\n    case nagramix\n    case proxy\n",
        "NagramiX settings group order",
    )
    replace_once(
        settings_items,
        """        items[.myProfile]!.append(PeerInfoScreenDisclosureItem(id: 0, text: presentationData.strings.Settings_MyProfile, icon: PresentationResourcesSettings.myProfile, action: {
            interaction.openSettings(.profile)
        }))
""" + "        \n" + """        if !settings.proxySettings.servers.isEmpty {
""",
        """        items[.myProfile]!.append(PeerInfoScreenDisclosureItem(id: 0, text: presentationData.strings.Settings_MyProfile, icon: PresentationResourcesSettings.myProfile, action: {
            interaction.openSettings(.profile)
        }))

        items[.nagramix]!.append(PeerInfoScreenDisclosureItem(id: 0, text: "Настройки NagramiX", icon: PresentationResourcesSettings.appearance, action: {
            interaction.openSettings(.nagramix)
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
                    PresentationAppIcon(name: "NagramiX1", imageName: "NagramiX1", isDefault: true),
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
        """                                case "PremiumTurbo":
                                    name = item.strings.Appearance_AppIconTurbo
                                default:
""",
        """                                case "PremiumTurbo":
                                    name = item.strings.Appearance_AppIconTurbo
                                case "NagramiX1":
                                    name = "NagramiX"
                                case "NagramiX2":
                                    name = "Закат"
                                case "NagramiX3":
                                    name = "Аврора"
                                case "NagramiX4":
                                    name = "Графит"
                                case "NagramiX5":
                                    name = "Янтарь"
                                case "NagramiX6":
                                    name = "Неон"
                                case "NagramiX7":
                                    name = "Лайм"
                                case "NagramiX8":
                                    name = "Рубин"
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
    "NagramiX1",
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

    print("Applied isolated NagramiX 0.1.6 tabs and app-icon overlay")
