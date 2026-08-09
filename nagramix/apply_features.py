#!/usr/bin/env python3
"""Apply the pinned NagramiX 0.1.3 feature overlay."""

from __future__ import annotations

import shutil
from pathlib import Path


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    # Keep multiline Swift replacements readable inside patches while ensuring
    # accidental diff markers never reach the generated source.
    new = new.replace("\n+", "\n")
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Pinned 0.1.3 patch anchor was not found ({label}): {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def localize_debug_file(path: Path, translations: dict[str, str], screen_title: tuple[str, str]) -> None:
    text = path.read_text(encoding="utf-8")
    import_anchor = "import AccountContext\n"
    helper = """import AccountContext

private func nagramixDebugTitle(_ presentationData: PresentationData, _ english: String, _ russian: String) -> String {
    return presentationData.strings.baseLanguageCode == "ru" ? russian : english
}
"""
    if import_anchor not in text:
        raise SystemExit(f"Debug localization import anchor was not found: {path}")
    text = text.replace(import_anchor, helper, 1)

    for english, russian in translations.items():
        old = f'title: "{english}"'
        new = f'title: nagramixDebugTitle(presentationData, "{english}", "{russian}")'
        if old not in text:
            raise SystemExit(f"Debug localization string was not found ({english}): {path}")
        text = text.replace(old, new)

    english_title, russian_title = screen_title
    old_title = f'title: .text("{english_title}")'
    new_title = f'title: .text(nagramixDebugTitle(presentationData, "{english_title}", "{russian_title}"))'
    if old_title not in text:
        raise SystemExit(f"Debug localization screen title was not found ({english_title}): {path}")
    text = text.replace(old_title, new_title, 1)
    path.write_text(text, encoding="utf-8")


def apply_features(source: Path) -> None:
    overlay = Path(__file__).resolve().parent

    settings_source = overlay / "Sources" / "NagramiXSettingsController.swift"
    settings_target = source / "submodules" / "SettingsUI" / "Sources" / settings_source.name
    shutil.copy2(settings_source, settings_target)

    coordinator_source = overlay / "Sources" / "ProxyAutoSwitchCoordinator.swift"
    coordinator_target = source / "submodules" / "TelegramCore" / "Sources" / "Settings" / coordinator_source.name
    shutil.copy2(coordinator_source, coordinator_target)

    model = source / "submodules" / "TelegramCore" / "Sources" / "SyncCore" / "SyncCore_ProxySettings.swift"
    replace_once(
        model,
        """    public var activeServer: ProxyServerSettings?\n    public var useForCalls: Bool\n""",
        """    public var activeServer: ProxyServerSettings?\n    public var useForCalls: Bool\n    public var autoSwitchEnabled: Bool\n    public var autoSwitchInterval: Int32\n""",
        "proxy model properties",
    )
    replace_once(
        model,
        """        return ProxySettings(enabled: false, servers: [], activeServer: nil, useForCalls: false)\n""",
        """        return ProxySettings(enabled: false, servers: [], activeServer: nil, useForCalls: false, autoSwitchEnabled: false, autoSwitchInterval: 15)\n""",
        "proxy defaults",
    )
    replace_once(
        model,
        """    public init(enabled: Bool, servers: [ProxyServerSettings], activeServer: ProxyServerSettings?, useForCalls: Bool) {\n        self.enabled = enabled\n        self.servers = servers\n        self.activeServer = activeServer\n        self.useForCalls = useForCalls\n    }\n""",
        """    public init(enabled: Bool, servers: [ProxyServerSettings], activeServer: ProxyServerSettings?, useForCalls: Bool, autoSwitchEnabled: Bool = false, autoSwitchInterval: Int32 = 15) {\n        self.enabled = enabled\n        self.servers = servers\n        self.activeServer = activeServer\n        self.useForCalls = useForCalls\n        self.autoSwitchEnabled = autoSwitchEnabled\n        self.autoSwitchInterval = autoSwitchInterval\n    }\n""",
        "proxy initializer",
    )
    replace_once(
        model,
        """        self.useForCalls = ((try? container.decode(Int32.self, forKey: \"useForCalls\")) ?? 0) != 0\n""",
        """        self.useForCalls = ((try? container.decode(Int32.self, forKey: \"useForCalls\")) ?? 0) != 0\n        self.autoSwitchEnabled = ((try? container.decode(Int32.self, forKey: \"nagramixAutoSwitchEnabled\")) ?? 0) != 0\n        let decodedInterval = (try? container.decode(Int32.self, forKey: \"nagramixAutoSwitchInterval\")) ?? 15\n        self.autoSwitchInterval = [15, 30, 60].contains(decodedInterval) ? decodedInterval : 15\n""",
        "proxy decoding",
    )
    replace_once(
        model,
        """        try container.encode((self.useForCalls ? 1 : 0) as Int32, forKey: \"useForCalls\")\n""",
        """        try container.encode((self.useForCalls ? 1 : 0) as Int32, forKey: \"useForCalls\")\n        try container.encode((self.autoSwitchEnabled ? 1 : 0) as Int32, forKey: \"nagramixAutoSwitchEnabled\")\n        try container.encode(self.autoSwitchInterval, forKey: \"nagramixAutoSwitchInterval\")\n""",
        "proxy encoding",
    )
    replace_once(
        model,
        """    public var effectiveActiveServer: ProxyServerSettings? {\n""",
        """    public var validatedAutoSwitchInterval: Double {\n        return Double([15, 30, 60].contains(self.autoSwitchInterval) ? self.autoSwitchInterval : 15)\n    }\n\n    public var effectiveActiveServer: ProxyServerSettings? {\n""",
        "validated interval",
    )

    account = source / "submodules" / "TelegramCore" / "Sources" / "Account" / "Account.swift"
    replace_once(
        account,
        """        }))\n\n        if !supplementary {\n""",
        """        }))\n        if !supplementary {\n            self.managedOperationsDisposable.add(ProxyAutoSwitchCoordinator(accountManager: accountManager, network: network))\n        }\n\n        if !supplementary {\n""",
        "account proxy coordinator",
    )

    ui = source / "submodules" / "SettingsUI" / "Sources" / "Data and Storage" / "ProxyListSettingsController.swift"
    replace_once(
        ui,
        """    let toggleUseForCalls: (Bool) -> Void\n    let shareProxyList: () -> Void\n""",
        """    let toggleUseForCalls: (Bool) -> Void\n    let toggleAutoSwitch: (Bool) -> Void\n    let selectNextAutoSwitchInterval: () -> Void\n    let shareProxyList: () -> Void\n""",
        "proxy UI arguments properties",
    )
    replace_once(
        ui,
        """    init(toggleEnabled: @escaping (Bool) -> Void, addNewServer: @escaping () -> Void, activateServer: @escaping (ProxyServerSettings) -> Void, editServer: @escaping (ProxyServerSettings) -> Void, removeServer: @escaping (ProxyServerSettings) -> Void, setServerWithRevealedOptions: @escaping (ProxyServerSettings?, ProxyServerSettings?) -> Void, toggleUseForCalls: @escaping (Bool) -> Void, shareProxyList: @escaping () -> Void) {\n""",
        """    init(toggleEnabled: @escaping (Bool) -> Void, addNewServer: @escaping () -> Void, activateServer: @escaping (ProxyServerSettings) -> Void, editServer: @escaping (ProxyServerSettings) -> Void, removeServer: @escaping (ProxyServerSettings?, ProxyServerSettings?) -> Void, setServerWithRevealedOptions: @escaping (ProxyServerSettings?, ProxyServerSettings?) -> Void, toggleUseForCalls: @escaping (Bool) -> Void, toggleAutoSwitch: @escaping (Bool) -> Void, selectNextAutoSwitchInterval: @escaping () -> Void, shareProxyList: @escaping () -> Void) {\n""",
        "proxy UI arguments initializer",
    )
    # Correct the remove-server closure type after expanding the initializer.
    replace_once(
        ui,
        "removeServer: @escaping (ProxyServerSettings?, ProxyServerSettings?) -> Void",
        "removeServer: @escaping (ProxyServerSettings) -> Void",
        "proxy UI remove closure type",
    )
    replace_once(
        ui,
        """        self.toggleUseForCalls = toggleUseForCalls\n        self.shareProxyList = shareProxyList\n""",
        """        self.toggleUseForCalls = toggleUseForCalls\n        self.toggleAutoSwitch = toggleAutoSwitch\n        self.selectNextAutoSwitchInterval = selectNextAutoSwitchInterval\n        self.shareProxyList = shareProxyList\n""",
        "proxy UI arguments assignments",
    )
    replace_once(ui, """    case share\n    case calls\n""", """    case share\n    case autoSwitch\n    case calls\n""", "proxy UI section")
    replace_once(
        ui,
        """    case shareProxyList(PresentationTheme, String)\n    case useForCalls(PresentationTheme, String, Bool)\n""",
        """    case shareProxyList(PresentationTheme, String)\n    case autoSwitch(PresentationTheme, String, Bool)\n    case autoSwitchInterval(PresentationTheme, String, String)\n    case autoSwitchInfo(PresentationTheme, String)\n    case useForCalls(PresentationTheme, String, Bool)\n""",
        "proxy UI entries",
    )
    replace_once(
        ui,
        """            case .shareProxyList:\n                return ProxySettingsControllerSection.share.rawValue\n            case .useForCalls, .useForCallsInfo:\n""",
        """            case .shareProxyList:\n                return ProxySettingsControllerSection.share.rawValue\n            case .autoSwitch, .autoSwitchInterval, .autoSwitchInfo:\n                return ProxySettingsControllerSection.autoSwitch.rawValue\n            case .useForCalls, .useForCallsInfo:\n""",
        "proxy UI entry sections",
    )
    replace_once(
        ui,
        """            case .shareProxyList:\n                return .index(3)\n            case .useForCalls:\n                return .index(4)\n            case .useForCallsInfo:\n                return .index(5)\n""",
        """            case .shareProxyList:\n                return .index(3)\n            case .autoSwitch:\n                return .index(4)\n            case .autoSwitchInterval:\n                return .index(5)\n            case .autoSwitchInfo:\n                return .index(6)\n            case .useForCalls:\n                return .index(7)\n            case .useForCallsInfo:\n                return .index(8)\n""",
        "proxy UI stable ids",
    )
    replace_once(
        ui,
        """            case let .useForCalls(lhsTheme, lhsText, lhsValue):\n""",
        """            case let .autoSwitch(lhsTheme, lhsText, lhsValue):\n                if case let .autoSwitch(rhsTheme, rhsText, rhsValue) = rhs, lhsTheme === rhsTheme, lhsText == rhsText, lhsValue == rhsValue {\n                    return true\n                } else {\n                    return false\n                }\n            case let .autoSwitchInterval(lhsTheme, lhsText, lhsValue):\n                if case let .autoSwitchInterval(rhsTheme, rhsText, rhsValue) = rhs, lhsTheme === rhsTheme, lhsText == rhsText, lhsValue == rhsValue {\n                    return true\n                } else {\n                    return false\n                }\n            case let .autoSwitchInfo(lhsTheme, lhsText):\n                if case let .autoSwitchInfo(rhsTheme, rhsText) = rhs, lhsTheme === rhsTheme, lhsText == rhsText {\n                    return true\n                } else {\n                    return false\n                }\n            case let .useForCalls(lhsTheme, lhsText, lhsValue):\n""",
        "proxy UI equality",
    )
    replace_once(
        ui,
        """            case .useForCalls:\n                switch rhs {\n                    case .enabled, .serversHeader, .addServer, .server, .shareProxyList, .useForCalls:\n                        return false\n                    default:\n                        return true\n                }\n            case .useForCallsInfo:\n                return false\n""",
        """            case .autoSwitch:\n                switch rhs {\n                    case .enabled, .serversHeader, .addServer, .server, .shareProxyList, .autoSwitch:\n                        return false\n                    default:\n                        return true\n                }\n            case .autoSwitchInterval:\n                switch rhs {\n                    case .enabled, .serversHeader, .addServer, .server, .shareProxyList, .autoSwitch, .autoSwitchInterval:\n                        return false\n                    default:\n                        return true\n                }\n            case .autoSwitchInfo:\n                switch rhs {\n                    case .useForCalls, .useForCallsInfo:\n                        return true\n                    default:\n                        return false\n                }\n            case .useForCalls:\n                switch rhs {\n                    case .useForCallsInfo:\n                        return true\n                    default:\n                        return false\n                }\n            case .useForCallsInfo:\n                return false\n""",
        "proxy UI ordering",
    )
    replace_once(
        ui,
        """            case let .useForCalls(_, text, value):\n""",
        """            case let .autoSwitch(_, text, value):\n                return ItemListSwitchItem(presentationData: presentationData, systemStyle: .glass, title: text, value: value, enableInteractiveChanges: true, enabled: true, sectionId: self.section, style: .blocks, updated: { value in\n                    arguments.toggleAutoSwitch(value)\n                })\n            case let .autoSwitchInterval(_, text, value):\n                return ItemListDisclosureItem(presentationData: presentationData, systemStyle: .glass, icon: nil, title: text, label: value, labelStyle: .text, sectionId: self.section, style: .blocks, disclosureStyle: .arrow, action: {\n                    arguments.selectNextAutoSwitchInterval()\n                })\n            case let .autoSwitchInfo(_, text):\n                return ItemListTextItem(presentationData: presentationData, text: .plain(text), sectionId: self.section)\n            case let .useForCalls(_, text, value):\n""",
        "proxy UI row rendering",
    )
    replace_once(
        ui,
        """    if let activeServer = proxySettings.activeServer, case .socks5 = activeServer.connection {\n""",
        """    if proxySettings.servers.count > 1 {\n        let isRussian = strings.baseLanguageCode == \"ru\"\n        entries.append(.autoSwitch(theme, isRussian ? \"Автопереключение прокси\" : \"Proxy Auto Switch\", proxySettings.autoSwitchEnabled))\n        if proxySettings.autoSwitchEnabled {\n            entries.append(.autoSwitchInterval(theme, isRussian ? \"Интервал проверки\" : \"Check Interval\", \"\\(Int(proxySettings.validatedAutoSwitchInterval)) \" + (isRussian ? \"сек.\" : \"sec\")))\n        }\n        entries.append(.autoSwitchInfo(theme, isRussian ? \"При потере соединения NagramiX проверит следующий сохранённый прокси. Исправный прокси не переключается.\" : \"When the connection is lost, NagramiX checks the next saved proxy. A healthy proxy is not rotated.\"))\n    }\n\n    if let activeServer = proxySettings.activeServer, case .socks5 = activeServer.connection {\n""",
        "proxy UI rows",
    )
    replace_once(
        ui,
        """    }, shareProxyList: {\n""",
        """    }, toggleAutoSwitch: { value in\n        let _ = updateProxySettingsInteractively(accountManager: accountManager, { current in\n            var current = current\n            current.autoSwitchEnabled = value && current.servers.count > 1\n            return current\n        }).start()\n    }, selectNextAutoSwitchInterval: {\n        let _ = updateProxySettingsInteractively(accountManager: accountManager, { current in\n            var current = current\n            let values: [Int32] = [15, 30, 60]\n            let index = values.firstIndex(of: current.autoSwitchInterval) ?? -1\n            current.autoSwitchInterval = values[(index + 1) % values.count]\n            return current\n        }).start()\n    }, shareProxyList: {\n""",
        "proxy UI actions",
    )

    debug_ui = source / "submodules" / "DebugSettingsUI" / "Sources"
    debug_controller = debug_ui / "DebugController.swift"
    localize_debug_file(
        debug_controller,
        {
            "Simulate Stickers Import": "Имитировать импорт стикеров",
            "Send Logs (Up to 40 MB)": "Отправить логи (до 40 МБ)",
            "Send Latest Logs (Up to 4 MB)": "Отправить последние логи (до 4 МБ)",
            "Send Share Logs (Up to 40 MB)": "Отправить логи общего доступа (до 40 МБ)",
            "Send Group Call Logs (Up to 40 MB)": "Отправить логи группового звонка (до 40 МБ)",
            "Send Notification Logs (Up to 40 MB)": "Отправить логи уведомлений (до 40 МБ)",
            "Send Critical Logs": "Отправить критические логи",
            "Send All Logs": "Отправить все логи",
            "Send Storage Stats": "Отправить статистику хранилища",
            "Via Telegram": "Через Telegram",
            "Via Email": "По электронной почте",
            "Accounts": "Аккаунты",
            "Log to File": "Записывать лог в файл",
            "Log to Console": "Выводить лог в консоль",
            "Remove Sensitive Data": "Удалять конфиденциальные данные",
            "Keep Chat Stack": "Сохранять стек чатов",
            "Skip read history": "Не отмечать историю прочитанной",
            "Show Typing": "Показывать набор текста",
            "Rating Debug": "Отладка рейтинга",
            "Crash when slow": "Сбой при медленной работе",
            "Crash on memory pressure": "Сбой при нехватке памяти",
            "Clear Tips": "Сбросить подсказки",
            "Log Language Recognition": "Логировать распознавание языка",
            "Reset Translation States": "Сбросить состояния перевода",
            "Reset Notifications": "Сбросить уведомления",
            "Crash": "Вызвать сбой",
            "Reload Saved Messages": "Перезагрузить сохранённые сообщения",
            "Clear Database": "Очистить базу данных",
            "Clear Database and Cache": "Очистить базу данных и кэш",
            "Reset Holes": "Сбросить пропуски",
            "Reset Tag Holes": "Сбросить пропуски тегов",
            "Reindex Unread Counters": "Переиндексировать счётчики непрочитанного",
            "Reset Cache Index [!]": "Сбросить индекс кэша [!]",
            "Reindex Cache": "Переиндексировать кэш",
            "Reset Biometrics Data": "Сбросить биометрические данные",
            "Allow Web View Inspection": "Разрешить проверку WebView",
            "Clear Web View Cache": "Очистить кэш WebView",
            "Optimize Database": "Оптимизировать базу данных",
            "Media Preview (Updated)": "Предпросмотр медиа (обновлённый)",
            "Knockout Wallpaper": "Прозрачные области обоев",
            "Experimental Compatibility": "Экспериментальная совместимость",
            "Debug Data Display": "Показывать отладочные данные",
            "Fake glass": "Имитация стекла",
            "Force clear glass": "Принудительно прозрачное стекло",
            "Debug Ripple": "Отладка эффекта волны",
            "Force Text Field v2": "Принудительно Text Field v2",
            "Inline UI": "Встроенный интерфейс",
            "Forum Tabs Debug": "Отладка вкладок форума",
            "Effect Overrides": "Переопределения эффектов",
            "Compressed Emoji Cache": "Сжатый кэш эмодзи",
            "Check Serialized Data": "Проверять сериализованные данные",
            "Enable Quick Reaction": "Включить быструю реакцию",
            "Live Stream V2": "Прямые трансляции V2",
            "[WIP] OS mic mute": "[В разработке] Системное отключение микрофона",
            "Enable Updates": "Включить обновления",
            "Local Translation": "Локальный перевод",
            "Video Cropping Optimization": "Оптимизация обрезки видео",
            "Network X [Restart App]": "Network X [перезапустить приложение]",
            "Download X [Restart App]": "Download X [перезапустить приложение]",
            "Restore Purchases": "Восстановить покупки",
            "Disable Relogin Tokens": "Отключить токены повторного входа",
        },
        ("Debug", "Отладка"),
    )
    replace_once(
        debug_controller,
        'text: "Now restart the app"',
        'text: nagramixDebugTitle(presentationData, "Now restart the app", "Теперь перезапустите приложение")',
        "debug restart alert",
    )
    debug_text = debug_controller.read_text(encoding="utf-8")
    secret_warning = 'ActionSheetTextItem(title: "All secret chats will be lost.")'
    if debug_text.count(secret_warning) != 2:
        raise SystemExit(f"Expected two Debug secret-chat warnings: {debug_controller}")
    debug_controller.write_text(
        debug_text.replace(
            secret_warning,
            'ActionSheetTextItem(title: nagramixDebugTitle(presentationData, "All secret chats will be lost.", "Все секретные чаты будут потеряны."))',
        ),
        encoding="utf-8",
    )
    localize_debug_file(
        debug_ui / "DebugAccountsController.swift",
        {
            "Login to another account": "Войти в другой аккаунт",
            "Production": "Основной сервер",
            "Test": "Тестовый сервер",
        },
        ("Accounts", "Аккаунты"),
    )

    peer_info_root = source / "submodules" / "TelegramUI" / "Components" / "PeerInfo" / "PeerInfoScreen" / "Sources"
    peer_info_screen = peer_info_root / "PeerInfoScreen.swift"
    replace_once(
        peer_info_screen,
        """    case proxy\n    case stories\n""",
        """    case proxy\n    case nagramix\n    case stories\n""",
        "NagramiX settings navigation section",
    )

    peer_info_items = peer_info_root / "PeerInfoSettingsItems.swift"
    replace_once(
        peer_info_items,
        """    items[.shortcuts]!.append(PeerInfoScreenDisclosureItem(id: 1, text: presentationData.strings.Settings_SavedMessages, icon: PresentationResourcesSettings.savedMessages, action: {\n""",
        """    let isRussian = presentationData.strings.baseLanguageCode == \"ru\"\n    items[.shortcuts]!.append(PeerInfoScreenDisclosureItem(id: 0, text: isRussian ? \"Настройки NagramiX\" : \"NagramiX Settings\", icon: PresentationResourcesSettings.appearance, action: {\n        interaction.openSettings(.nagramix)\n    }))\n    items[.shortcuts]!.append(PeerInfoScreenDisclosureItem(id: 1, text: presentationData.strings.Settings_SavedMessages, icon: PresentationResourcesSettings.savedMessages, action: {\n""",
        "NagramiX settings main row",
    )

    peer_info_actions = peer_info_root / "PeerInfoScreenSettingsActions.swift"
    replace_once(
        peer_info_actions,
        """        case .proxy:\n            self.controller?.push(proxySettingsController(context: self.context))\n        case .profile:\n""",
        """        case .proxy:\n            self.controller?.push(proxySettingsController(context: self.context))\n        case .nagramix:\n            push(nagramiXSettingsController(context: self.context))\n        case .profile:\n""",
        "NagramiX settings navigation action",
    )

    root_controller = source / "submodules" / "TelegramUI" / "Sources" / "TelegramRootController.swift"
    replace_once(
        root_controller,
        """    private var applicationInFocusDisposable: Disposable?\n    private var storyUploadEventsDisposable: Disposable?\n""",
        """    private var applicationInFocusDisposable: Disposable?\n    private var storyUploadEventsDisposable: Disposable?\n    private var nagramixPreferencesObserver: NSObjectProtocol?\n""",
        "root tab preferences observer property",
    )
    replace_once(
        root_controller,
        """        super.init(mode: .automaticMasterDetail, theme: NavigationControllerTheme(presentationTheme: self.presentationData.theme))\n        \n        self.presentationDataDisposable = (context.sharedContext.presentationData\n""",
        """        super.init(mode: .automaticMasterDetail, theme: NavigationControllerTheme(presentationTheme: self.presentationData.theme))\n+        \n+        self.nagramixPreferencesObserver = NotificationCenter.default.addObserver(forName: Notification.Name("NagramiXPreferencesChanged"), object: nil, queue: .main, using: { [weak self] _ in\n+            self?.updateRootControllers(showCallsTab: false)\n+        })\n+        \n+        self.presentationDataDisposable = (context.sharedContext.presentationData\n""",
        "root tab preferences observer setup",
    )
    replace_once(
        root_controller,
        """        self.storyUploadEventsDisposable?.dispose()\n    }\n""",
        """        self.storyUploadEventsDisposable?.dispose()\n+        if let nagramixPreferencesObserver = self.nagramixPreferencesObserver {\n+            NotificationCenter.default.removeObserver(nagramixPreferencesObserver)\n+        }\n+    }\n""",
        "root tab preferences observer cleanup",
    )
    replace_once(
        root_controller,
        """        controllers.append(contactsController)\n        \n        if showCallsTab {\n            controllers.append(callListController)\n        }\n        controllers.append(chatListController)\n""",
        """        if UserDefaults.standard.bool(forKey: "nagramix.showContactsTab") {\n+            controllers.append(contactsController)\n+        }\n+        \n+        if UserDefaults.standard.bool(forKey: "nagramix.showCallsTab") {\n+            controllers.append(callListController)\n+        }\n+        controllers.append(chatListController)\n""",
        "default NagramiX root tabs",
    )
    replace_once(
        root_controller,
        """        var controllers: [ViewController] = []\n        controllers.append(self.contactsController!)\n        if showCallsTab {\n            controllers.append(self.callListController!)\n        }\n        controllers.append(self.chatListController!)\n""",
        """        var controllers: [ViewController] = []\n+        if UserDefaults.standard.bool(forKey: "nagramix.showContactsTab"), let contactsController = self.contactsController {\n+            controllers.append(contactsController)\n+        }\n+        if UserDefaults.standard.bool(forKey: "nagramix.showCallsTab"), let callListController = self.callListController {\n+            controllers.append(callListController)\n+        }\n+        controllers.append(self.chatListController!)\n""",
        "updated NagramiX root tabs",
    )

    message_timestamp = source / "submodules" / "TelegramUI" / "Components" / "Chat" / "ChatMessageDateAndStatusNode" / "Sources" / "StringForMessageTimestampStatus.swift"
    replace_once(
        message_timestamp,
        """    var dateText = stringForMessageTimestamp(timestamp: timestamp, dateTimeFormat: dateTimeFormat)\n""",
        """    var dateText = stringForMessageTimestamp(timestamp: timestamp, dateTimeFormat: dateTimeFormat, withSeconds: UserDefaults.standard.bool(forKey: "nagramix.showMessageSeconds"))\n""",
        "message timestamp seconds",
    )

    account_context = source / "submodules" / "TelegramUI" / "Sources" / "AccountContext.swift"
    replace_once(
        account_context,
        """    public func requestCall(peerId: PeerId, isVideo: Bool, completion: @escaping () -> Void) {\n        guard let callResult = self.sharedContext.callManager?.requestCall(context: self, peerId: peerId, isVideo: isVideo, endCurrentIfAny: false) else {\n""",
        """    public func requestCall(peerId: PeerId, isVideo: Bool, completion: @escaping () -> Void) {\n+        if UserDefaults.standard.bool(forKey: "nagramix.confirmCalls") {\n+            let presentationData = self.sharedContext.currentPresentationData.with { $0 }\n+            let isRussian = presentationData.strings.baseLanguageCode == "ru"\n+            self.sharedContext.mainWindow?.present(textAlertController(context: self, title: isRussian ? "Подтверждение вызова" : "Confirm Call", text: isRussian ? (isVideo ? "Начать видеозвонок?" : "Начать голосовой звонок?") : (isVideo ? "Start a video call?" : "Start a voice call?"), actions: [\n+                TextAlertAction(type: .genericAction, title: presentationData.strings.Common_Cancel, action: {}),\n+                TextAlertAction(type: .defaultAction, title: isRussian ? "Позвонить" : "Call", action: { [weak self] in\n+                    self?.nagramixRequestCall(peerId: peerId, isVideo: isVideo, completion: completion)\n+                })\n+            ]), on: .root)\n+        } else {\n+            self.nagramixRequestCall(peerId: peerId, isVideo: isVideo, completion: completion)\n+        }\n+    }\n+    \n+    private func nagramixRequestCall(peerId: PeerId, isVideo: Bool, completion: @escaping () -> Void) {\n+        guard let callResult = self.sharedContext.callManager?.requestCall(context: self, peerId: peerId, isVideo: isVideo, endCurrentIfAny: false) else {\n""",
        "call confirmation wrapper",
    )

    peer_info_header = peer_info_root / "PeerInfoHeaderNode.swift"
    replace_once(
        peer_info_header,
        """            if self.isSettings, case let .user(user) = peer {\n                var subtitle = formatPhoneNumber(context: self.context, number: user.phone ?? "")\n                \n                if let mainUsername = user.addressName, !mainUsername.isEmpty {\n                    subtitle = "\\(subtitle) • @\\(mainUsername)"\n                }\n""",
        """            if self.isSettings, case let .user(user) = peer {\n+                let hidePhoneNumber = UserDefaults.standard.bool(forKey: "nagramix.hidePhoneNumber")\n+                var subtitle = hidePhoneNumber ? "••••••••" : formatPhoneNumber(context: self.context, number: user.phone ?? "")\n+                \n+                if let mainUsername = user.addressName, !mainUsername.isEmpty {\n+                    subtitle = hidePhoneNumber ? "@\\(mainUsername)" : "\\(subtitle) • @\\(mainUsername)"\n+                }\n""",
        "hide own phone in settings header",
    )
    replace_once(
        peer_info_items,
        """        items[.info]!.append(PeerInfoScreenDisclosureItem(id: ItemPhoneNumber, label: .text(user.phone.flatMap({ formatPhoneNumber(context: context, number: $0) }) ?? ""), text: presentationData.strings.Settings_PhoneNumber, icon: PresentationResourcesSettings.recentCalls, action: {\n""",
        """        let nagramixPhoneLabel = UserDefaults.standard.bool(forKey: "nagramix.hidePhoneNumber") ? "••••••••" : (user.phone.flatMap({ formatPhoneNumber(context: context, number: $0) }) ?? "")\n+        items[.info]!.append(PeerInfoScreenDisclosureItem(id: ItemPhoneNumber, label: .text(nagramixPhoneLabel), text: presentationData.strings.Settings_PhoneNumber, icon: PresentationResourcesSettings.recentCalls, action: {\n""",
        "hide own phone in settings list",
    )

    peer_profile_items = peer_info_root / "PeerInfoProfileItems.swift"
    replace_once(
        peer_profile_items,
        """    let birthdayContextAction: (ASDisplayNode, ContextGesture?, CGPoint?) -> Void = { node, gesture, _ in\n        interaction.openBirthdayContextMenu(node, gesture)\n    }\n    \n    if case let .user(user) = data.peer {\n""",
        """    let birthdayContextAction: (ASDisplayNode, ContextGesture?, CGPoint?) -> Void = { node, gesture, _ in\n+        interaction.openBirthdayContextMenu(node, gesture)\n+    }\n+    \n+    if UserDefaults.standard.bool(forKey: "nagramix.showPeerIds"), let peer = data.peer {\n+        items[currentPeerInfoSection]!.append(PeerInfoScreenLabeledValueItem(id: 900, label: "ID", text: "\\(peer.id.toInt64())", textColor: .accent, action: { _, _ in\n+            UIPasteboard.general.string = "\\(peer.id.toInt64())"\n+        }, requestLayout: { animated in\n+            interaction.requestLayout(animated)\n+        }))\n+        if let resource = peer.profileImageRepresentations.first?.resource as? CloudPeerPhotoSizeMediaResource {\n+            items[currentPeerInfoSection]!.append(PeerInfoScreenLabeledValueItem(id: 901, label: "DC", text: "\\(resource.datacenterId)", textColor: .accent, action: nil, requestLayout: { animated in\n+                interaction.requestLayout(animated)\n+            }))\n+        }\n+    }\n+    \n+    if case let .user(user) = data.peer {\n""",
        "profile id and avatar datacenter",
    )

    video_message_camera = source / "submodules" / "TelegramUI" / "Components" / "VideoMessageCameraScreen" / "Sources" / "VideoMessageCameraScreen.swift"
    replace_once(
        video_message_camera,
        """            let isDualCameraEnabled = Camera.isDualCameraSupported(forRoundVideo: true)\n            let isFrontPosition = "".isEmpty\n""",
        """            let isDualCameraEnabled = Camera.isDualCameraSupported(forRoundVideo: true)\n+            let isFrontPosition = !UserDefaults.standard.bool(forKey: "nagramix.preferBackCamera")\n""",
        "video message default camera",
    )

    chat_list_item = source / "submodules" / "ChatListUI" / "Sources" / "Node" / "ChatListItem.swift"
    replace_once(
        chat_list_item,
        """                maximumNumberOfLines: (authorAttributedString == nil && itemTags.isEmpty && forumThread == nil && topForumTopicItems.isEmpty) ? 2 : 1,\n""",
        """                maximumNumberOfLines: UserDefaults.standard.bool(forKey: "nagramix.compactMessagePreview") ? 1 : ((authorAttributedString == nil && itemTags.isEmpty && forumThread == nil && topForumTopicItems.isEmpty) ? 2 : 1),\n""",
        "compact chat preview",
    )
    replace_once(
        chat_list_item,
        """                itemHeight += authorSpacing\n            }\n                        \n            let rawContentRect = CGRect""",
        """                itemHeight += authorSpacing\n+            }\n+            if UserDefaults.standard.bool(forKey: "nagramix.compactChatList") {\n+                itemHeight = max(56.0, itemHeight - 10.0)\n+            }\n+                        \n+            let rawContentRect = CGRect""",
        "compact chat list height",
    )

    panel_interaction = source / "submodules" / "ChatPresentationInterfaceState" / "Sources" / "ChatPanelInterfaceInteraction.swift"
    replace_once(
        panel_interaction,
        """    public let beginMessageSelection: ([EngineMessage.Id], @escaping (ContainedViewLayoutTransition) -> Void) -> Void\n    public let cancelMessageSelection: (ContainedViewLayoutTransition) -> Void\n""",
        """    public let beginMessageSelection: ([EngineMessage.Id], @escaping (ContainedViewLayoutTransition) -> Void) -> Void\n+    public let selectMessagesFromAuthor: (EnginePeer.Id) -> Void\n+    public let cancelMessageSelection: (ContainedViewLayoutTransition) -> Void\n""",
        "select from author interaction property",
    )
    replace_once(
        panel_interaction,
        """        chatController: @escaping () -> ViewController?,\n        statuses: ChatPanelInterfaceInteractionStatuses?\n    ) {\n""",
        """        chatController: @escaping () -> ViewController?,\n+        statuses: ChatPanelInterfaceInteractionStatuses?,\n+        selectMessagesFromAuthor: @escaping (EnginePeer.Id) -> Void = { _ in }\n+    ) {\n""",
        "select from author interaction initializer",
    )
    replace_once(
        panel_interaction,
        """        self.beginMessageSelection = beginMessageSelection\n        self.cancelMessageSelection = cancelMessageSelection\n""",
        """        self.beginMessageSelection = beginMessageSelection\n+        self.selectMessagesFromAuthor = selectMessagesFromAuthor\n+        self.cancelMessageSelection = cancelMessageSelection\n""",
        "select from author interaction assignment",
    )

    chat_load = source / "submodules" / "TelegramUI" / "Sources" / "Chat" / "ChatControllerLoadDisplayNode.swift"
    replace_once(
        chat_load,
        """                let forwardMessageIds = messages.map { $0.id }.sorted()\n                strongSelf.forwardMessages(messageIds: forwardMessageIds)\n            }\n        }, updateForwardOptionsState:""",
        """                let forwardMessageIds = messages.map { $0.id }.sorted()\n+                let hideNames = UserDefaults.standard.bool(forKey: "nagramix.forwardHideNamesOnce")\n+                UserDefaults.standard.removeObject(forKey: "nagramix.forwardHideNamesOnce")\n+                let options = hideNames ? ChatInterfaceForwardOptionsState(hideNames: true, hideCaptions: false, unhideNamesOnCaptionChange: false) : nil\n+                strongSelf.forwardMessages(messageIds: forwardMessageIds, options: options)\n+            }\n+        }, updateForwardOptionsState:""",
        "forward mode handoff",
    )
    replace_once(
        chat_load,
        """        }, statuses: ChatPanelInterfaceInteractionStatuses(editingMessage: self.editingMessage.get(), startingBot: self.startingBot.get(), unblockingPeer: self.unblockingPeer.get(), searching: self.searching.get(), loadingMessage: self.loadingMessage.get(), inlineSearch: self.performingInlineSearch.get()))\n""",
        """        }, statuses: ChatPanelInterfaceInteractionStatuses(editingMessage: self.editingMessage.get(), startingBot: self.startingBot.get(), unblockingPeer: self.unblockingPeer.get(), searching: self.searching.get(), loadingMessage: self.loadingMessage.get(), inlineSearch: self.performingInlineSearch.get()), selectMessagesFromAuthor: { [weak self] authorId in\n+            guard let self else {\n+                return\n+            }\n+            var ids: [EngineMessage.Id] = []\n+            self.chatDisplayNode.historyNode.forEachItemNode { itemNode in\n+                guard let itemNode = itemNode as? ChatMessageItemView, let item = itemNode.item else {\n+                    return\n+                }\n+                for (message, _) in item.content {\n+                    if message.author?.id == authorId {\n+                        ids.append(message.id)\n+                    }\n+                }\n+            }\n+            let uniqueIds = Array(Set(ids)).sorted()\n+            if !uniqueIds.isEmpty {\n+                self.interfaceInteraction?.beginMessageSelection(uniqueIds, { _ in })\n+            }\n+        })\n""",
        "select loaded messages from author",
    )

    context_menus = source / "submodules" / "TelegramUI" / "Sources" / "ChatInterfaceStateContextMenus.swift"
    replace_once(
        context_menus,
        """        if data.messageActions.options.contains(.forward) {\n            if !isCopyProtected {\n                actions.append(.action(ContextMenuActionItem(text: chatPresentationInterfaceState.strings.Conversation_ContextMenuForward, icon: { theme in\n                    return generateTintedImage(image: UIImage(bundleImageName: "Chat/Context Menu/Forward"), color: theme.actionSheet.primaryTextColor)\n                }, action: { _, f in\n                    interfaceInteraction.forwardMessages(selectAll || isImage ? messages : [message])\n                    f(.dismissWithoutContent)\n                })))\n            }\n        }\n""",
        """        if data.messageActions.options.contains(.forward) {\n+            if !isCopyProtected {\n+                let isRussian = chatPresentationInterfaceState.strings.baseLanguageCode == "ru"\n+                actions.append(.action(ContextMenuActionItem(text: isRussian ? "Переслать" : "Forward without Author", icon: { theme in\n+                    return generateTintedImage(image: UIImage(bundleImageName: "Chat/Context Menu/Forward"), color: theme.actionSheet.primaryTextColor)\n+                }, action: { _, f in\n+                    UserDefaults.standard.set(true, forKey: "nagramix.forwardHideNamesOnce")\n+                    interfaceInteraction.forwardMessages(selectAll || isImage ? messages : [message])\n+                    f(.dismissWithoutContent)\n+                })))\n+                actions.append(.action(ContextMenuActionItem(text: isRussian ? "Переслать от" : "Forward with Author", icon: { theme in\n+                    return generateTintedImage(image: UIImage(bundleImageName: "Chat/Context Menu/Forward"), color: theme.actionSheet.primaryTextColor)\n+                }, action: { _, f in\n+                    UserDefaults.standard.removeObject(forKey: "nagramix.forwardHideNamesOnce")\n+                    interfaceInteraction.forwardMessages(selectAll || isImage ? messages : [message])\n+                    f(.dismissWithoutContent)\n+                })))\n+                actions.append(.action(ContextMenuActionItem(text: isRussian ? "Сохранить в Избранное" : "Save to Saved Messages", icon: { theme in\n+                    return generateTintedImage(image: UIImage(bundleImageName: "Chat/Context Menu/Fave"), color: theme.actionSheet.primaryTextColor)\n+                }, action: { _, f in\n+                    let selectedMessages = selectAll || isImage ? messages : [message]\n+                    let enqueue = selectedMessages.map { value in\n+                        return EnqueueMessage.forward(source: value.id, threadId: nil, grouping: .auto, attributes: [], correlationId: nil)\n+                    }\n+                    let _ = enqueueMessages(account: context.account, peerId: context.account.peerId, messages: enqueue).startStandalone()\n+                    controllerInteraction.displayUndo(.forward(savedMessages: true, text: chatPresentationInterfaceState.strings.Conversation_ForwardTooltip_SavedMessages_One))\n+                    f(.dismissWithoutContent)\n+                })))\n+            }\n+        }\n""",
        "NagramiX forward and saved messages actions",
    )
    replace_once(
        context_menus,
        """        if !isCopyProtected {\n            for media in message.effectiveMedia {\n                if let file = media as? TelegramMediaFile {\n                    if file.isMusic {\n                        actions.append(.action(ContextMenuActionItem(text: chatPresentationInterfaceState.strings.Conversation_SaveToFiles, icon: { theme in\n                            return generateTintedImage(image: UIImage(bundleImageName: "Chat/Context Menu/Save"), color: theme.actionSheet.primaryTextColor)\n                        }, action: { _, f in\n                            controllerInteraction.saveMediaToFiles(message.id)\n                            f(.default)\n                        })))\n                    }\n                    break\n                }\n            }\n        }\n""",
        """        if !isCopyProtected {\n+            let hasSavableAttachment = message.effectiveMedia.contains(where: { media in\n+                return media is TelegramMediaFile || media is TelegramMediaImage\n+            })\n+            if hasSavableAttachment {\n+                actions.append(.action(ContextMenuActionItem(text: chatPresentationInterfaceState.strings.baseLanguageCode == "ru" ? "Сохранить в Файлы" : "Save to Files", icon: { theme in\n+                    return generateTintedImage(image: UIImage(bundleImageName: "Chat/Context Menu/Save"), color: theme.actionSheet.primaryTextColor)\n+                }, action: { _, f in\n+                    controllerInteraction.saveMediaToFiles(message.id)\n+                    f(.default)\n+                })))\n+            }\n+        }\n""",
        "save any attachment to files",
    )
    replace_once(
        context_menus,
        """                actions.append(.action(ContextMenuActionItem(text: chatPresentationInterfaceState.strings.Conversation_ContextMenuSelect, icon: { theme in\n                    return generateTintedImage(image: UIImage(bundleImageName: "Chat/Context Menu/Select"), color: theme.actionSheet.primaryTextColor)\n                }, action: { _, f in\n                    interfaceInteraction.beginMessageSelection(selectAll ? messages.map { $0.id } : [message.id], { transition in\n                        f(.custom(transition))\n                    })\n                })))\n            }\n""",
        """                actions.append(.action(ContextMenuActionItem(text: chatPresentationInterfaceState.strings.Conversation_ContextMenuSelect, icon: { theme in\n+                    return generateTintedImage(image: UIImage(bundleImageName: "Chat/Context Menu/Select"), color: theme.actionSheet.primaryTextColor)\n+                }, action: { _, f in\n+                    interfaceInteraction.beginMessageSelection(selectAll ? messages.map { $0.id } : [message.id], { transition in\n+                        f(.custom(transition))\n+                    })\n+                })))\n+                if let authorId = message.author?.id {\n+                    actions.append(.action(ContextMenuActionItem(text: chatPresentationInterfaceState.strings.baseLanguageCode == "ru" ? "Выбрать от" : "Select from Author", icon: { theme in\n+                        return generateTintedImage(image: UIImage(bundleImageName: "Chat/Context Menu/SelectAll"), color: theme.actionSheet.primaryTextColor)\n+                    }, action: { _, f in\n+                        interfaceInteraction.selectMessagesFromAuthor(authorId)\n+                        f(.dismissWithoutContent)\n+                    })))\n+                }\n+            }\n""",
        "select from author menu action",
    )

    print("Applied NagramiX feature overlay, including Russian Debug UI")
