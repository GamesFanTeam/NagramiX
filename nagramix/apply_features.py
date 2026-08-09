#!/usr/bin/env python3
"""Apply the pinned NagramiX 0.1.2 feature overlay."""

from __future__ import annotations

import shutil
from pathlib import Path


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Pinned 0.1.2 patch anchor was not found ({label}): {path}")
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

    print("Applied NagramiX feature overlay, including Russian Debug UI")
