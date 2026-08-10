#!/usr/bin/env python3
"""Apply the pinned NagramiX 0.1.5 feature overlay."""

from __future__ import annotations

import shutil
from pathlib import Path


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    # Keep multiline Swift replacements readable inside patches while ensuring
    # accidental diff markers never reach the generated source.
    new = new.replace("\n+", "\n")
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Pinned 0.1.5 patch anchor was not found ({label}): {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_exact_count(path: Path, old: str, new: str, expected_count: int, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    actual_count = text.count(old)
    if actual_count != expected_count:
        raise SystemExit(
            f"Pinned 0.1.5 patch anchor count mismatch ({label}): "
            f"expected {expected_count}, found {actual_count}: {path}"
        )
    path.write_text(text.replace(old, new), encoding="utf-8")


def localize_debug_file(path: Path, translations: dict[str, str], screen_title: tuple[str, str]) -> None:
    text = path.read_text(encoding="utf-8")
    import_anchor = "import AccountContext\n"
    helper = """import AccountContext

private func nagramixDebugTitle(_ presentationData: PresentationData, _ english: String, _ russian: String) -> String {
    return presentationData.strings.baseLanguageCode == "ru" ? russian : english
}

private func nagramixDebugTitle(_ presentationData: ItemListPresentationData, _ english: String, _ russian: String) -> String {
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

    splash_controller = source / "submodules" / "AuthorizationUI" / "Sources" / "AuthorizationSequenceSplashController.swift"
    replace_once(
        splash_controller,
        """    private let startButton: SolidRoundedButtonNode\n""",
        """    private let startButton: SolidRoundedButtonNode\n    private var nagramixLogoView: UIImageView?\n""",
        "NagramiX intro logo property",
    )
    replace_once(
        splash_controller,
        """        self.startButton = SolidRoundedButtonNode(title: "Start Messaging", theme: SolidRoundedButtonTheme(theme: theme), glass: false, height: 50.0, cornerRadius: 50.0 * 0.5, isShimmering: true)\n""",
        """        self.startButton = SolidRoundedButtonNode(title: "Начать общение", theme: SolidRoundedButtonTheme(theme: theme), glass: false, height: 50.0, cornerRadius: 50.0 * 0.5, isShimmering: true)\n""",
        "Russian NagramiX intro button",
    )
    replace_once(
        splash_controller,
        """        self.controller.startMessaging = { [weak self] in\n            self?.activateLocalization("en")\n        }\n""",
        """        self.controller.startMessaging = { [weak self] in\n            self?.activateLocalization("ru")\n        }\n""",
        "Russian first-launch localization",
    )
    replace_once(
        splash_controller,
        """        self.startButton.pressed = { [weak self] in\n            self?.activateLocalization("en")\n        }\n""",
        """        self.startButton.pressed = { [weak self] in\n            self?.activateLocalization("ru")\n        }\n""",
        "Russian first-launch button localization",
    )
    replace_once(
        splash_controller,
        """            self.displayNode.view.addSubview(self.controller.view)\n            if let layout = self.validLayout {\n""",
        """            self.displayNode.view.addSubview(self.controller.view)\n            if self.nagramixLogoView == nil, let image = UIImage(named: "NagramiX-Intro") {\n                let imageView = UIImageView(image: image)\n                imageView.contentMode = .scaleAspectFit\n                imageView.isUserInteractionEnabled = false\n                self.controller.view.addSubview(imageView)\n                self.nagramixLogoView = imageView\n            }\n            if let layout = self.validLayout {\n                if let logoView = self.nagramixLogoView {\n                    let logoSide = min(320.0, max(180.0, layout.size.width - 64.0))\n                    let logoY = max(layout.safeInsets.top + 12.0, 36.0)\n                    logoView.frame = CGRect(x: floor((layout.size.width - logoSide) * 0.5), y: logoY, width: logoSide, height: logoSide)\n                    self.controller.view.bringSubviewToFront(logoView)\n                }\n""",
        "NagramiX intro logo setup",
    )
    replace_once(
        splash_controller,
        """    var animationSnapshot: UIView? {\n        return self.controller.createAnimationSnapshot()\n    }\n""",
        """    var animationSnapshot: UIView? {\n        if let logoView = self.nagramixLogoView, let snapshot = logoView.snapshotView(afterScreenUpdates: false) {\n            snapshot.frame = logoView.frame\n            return snapshot\n        }\n        return self.controller.createAnimationSnapshot()\n    }\n""",
        "NagramiX intro logo transition snapshot",
    )
    replace_once(
        splash_controller,
        """        let controllerFrame = CGRect(origin: CGPoint(), size: layout.size)\n        self.controller.defaultFrame = controllerFrame\n""",
        """        let controllerFrame = CGRect(origin: CGPoint(), size: layout.size)\n        self.controller.defaultFrame = controllerFrame\n        if let logoView = self.nagramixLogoView {\n            let logoSide = min(320.0, max(180.0, layout.size.width - 64.0))\n            let logoY = max(layout.safeInsets.top + 12.0, 36.0)\n            logoView.frame = CGRect(x: floor((layout.size.width - logoSide) * 0.5), y: logoY, width: logoSide, height: logoSide)\n            self.controller.view.bringSubviewToFront(logoView)\n        }\n""",
        "NagramiX intro logo layout",
    )

    intro_controller = source / "submodules" / "RMIntro" / "Sources" / "platform" / "ios" / "RMIntroViewController.m"
    replace_once(
        intro_controller,
        """        _headlines = @[ _englishStrings[@"Tour.Title1"], _englishStrings[@"Tour.Title2"],  _englishStrings[@"Tour.Title6"], _englishStrings[@"Tour.Title3"], _englishStrings[@"Tour.Title4"], _englishStrings[@"Tour.Title5"]];\n        _descriptions = @[_englishStrings[@"Tour.Text1"], _englishStrings[@"Tour.Text2"],  _englishStrings[@"Tour.Text6"], _englishStrings[@"Tour.Text3"], _englishStrings[@"Tour.Text4"], _englishStrings[@"Tour.Text5"]];\n""",
        """        _headlines = @[ @"NagramiX", @"Быстро", @"Расширенно", @"Мощно", @"Безопасно", @"Облачно" ];\n        _descriptions = @[\n            @"Расширенный Telegram-клиент для iOS.\\nБыстро, бесплатно и безопасно.",\n            @"Сообщения доставляются быстро даже при слабом соединении.",\n            @"Дополнительные настройки позволяют управлять приложением по своим правилам.",\n            @"Отправляйте сообщения, фотографии, видео и файлы.",\n            @"Ваши сообщения защищены средствами Telegram.",\n            @"Получайте доступ к чатам со всех своих устройств."\n        ];\n""",
        "Russian NagramiX intro texts",
    )

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
    replace_once(
        root_controller,
        """        tabBarController.setControllers(controllers, selectedIndex: restoreSettignsController != nil ? (controllers.count - 1) : (controllers.count - 2))
""",
        """        let showNagramiXTabNames = UserDefaults.standard.object(forKey: "nagramix.showTabNames") == nil || UserDefaults.standard.bool(forKey: "nagramix.showTabNames")
        contactsController.tabBarItem.title = showNagramiXTabNames ? self.presentationData.strings.Contacts_Title : nil
        callListController.tabBarItem.title = showNagramiXTabNames ? self.presentationData.strings.Calls_TabTitle : nil
        chatListController.tabBarItem.title = showNagramiXTabNames ? self.presentationData.strings.DialogList_Title : nil
        accountSettingsController.tabBarItem.title = showNagramiXTabNames ? self.presentationData.strings.Settings_Title : nil
        tabBarController.setControllers(controllers, selectedIndex: restoreSettignsController != nil ? (controllers.count - 1) : (controllers.count - 2))
        tabBarController.updateIsTabBarHidden(UserDefaults.standard.bool(forKey: "nagramix.hideTabBar"), transition: .immediate)

""",
        "NagramiX initial tab bar appearance",
    )
    replace_once(
        root_controller,
        """        controllers.append(self.accountSettingsController!)
""",
        """        controllers.append(self.accountSettingsController!)

        let showNagramiXTabNames = UserDefaults.standard.object(forKey: "nagramix.showTabNames") == nil || UserDefaults.standard.bool(forKey: "nagramix.showTabNames")
        self.contactsController?.tabBarItem.title = showNagramiXTabNames ? self.presentationData.strings.Contacts_Title : nil
        self.callListController?.tabBarItem.title = showNagramiXTabNames ? self.presentationData.strings.Calls_TabTitle : nil
        self.chatListController?.tabBarItem.title = showNagramiXTabNames ? self.presentationData.strings.DialogList_Title : nil
        self.accountSettingsController?.tabBarItem.title = showNagramiXTabNames ? self.presentationData.strings.Settings_Title : nil
""",
        "NagramiX live tab bar appearance",
    )
    replace_once(
        root_controller,
        """        rootTabController.setControllers(controllers, selectedIndex: nil)
""",
        """        rootTabController.setControllers(controllers, selectedIndex: nil)
        rootTabController.updateIsTabBarHidden(UserDefaults.standard.bool(forKey: "nagramix.hideTabBar"), transition: .animated(duration: 0.25, curve: .easeInOut))
""",
        "NagramiX live tab bar visibility",
    )

    chat_list_controller_node = source / "submodules" / "ChatListUI" / "Sources" / "ChatListControllerNode.swift"
    replace_once(
        chat_list_controller_node,
        """            if let controller = self.controller, let storySubscriptions = controller.orderedStorySubscriptions, shouldDisplayStoriesInChatListHeader(storySubscriptions: storySubscriptions, isHidden: controller.location == .chatList(groupId: .archive)) {
                effectiveStorySubscriptions = controller.orderedStorySubscriptions
""",
        """            if !UserDefaults.standard.bool(forKey: "nagramix.hideStories"), let controller = self.controller, let storySubscriptions = controller.orderedStorySubscriptions, shouldDisplayStoriesInChatListHeader(storySubscriptions: storySubscriptions, isHidden: controller.location == .chatList(groupId: .archive)) {
                effectiveStorySubscriptions = controller.orderedStorySubscriptions
""",
        "hide stories in chat list header",
    )
    replace_once(
        chat_list_controller_node,
        """                search: ChatListNavigationBar.Search(isEnabled: true),
""",
        """                search: ChatListNavigationBar.Search(isEnabled: UserDefaults.standard.object(forKey: "nagramix.showSearchButton") == nil || UserDefaults.standard.bool(forKey: "nagramix.showSearchButton")),
""",
        "NagramiX search button visibility",
    )
    replace_once(
        chat_list_controller_node,
        """                if case .compact = layout.metrics.widthClass, self.controller?.isStoryPostingAvailable == true && !(self.context.sharedContext.callManager?.hasActiveCall ?? false) {
""",
        """                if case .compact = layout.metrics.widthClass, !UserDefaults.standard.bool(forKey: "nagramix.disableStoryCameraSwipe"), self.controller?.isStoryPostingAvailable == true && !(self.context.sharedContext.callManager?.hasActiveCall ?? false) {
""",
        "disable swipe to story camera",
    )

    chat_list_controller = source / "submodules" / "ChatListUI" / "Sources" / "ChatListController.swift"
    replace_once(
        chat_list_controller,
        """            var resolvedItems = filterItems
            if case .chatList(.root) = strongSelf.location {
            } else {
                resolvedItems = []
            }
""",
        """            var resolvedItems = filterItems
            if case .chatList(.root) = strongSelf.location {
            } else {
                resolvedItems = []
            }
            if UserDefaults.standard.bool(forKey: "nagramix.hideAllChatsFolder"), resolvedItems.contains(where: { entry in
                if case .filter = entry {
                    return true
                }
                return false
            }) {
                resolvedItems.removeAll(where: { entry in
                    if case .all = entry {
                        return true
                    }
                    return false
                })
            }
""",
        "hide All Chats folder when custom folders exist",
    )
    replace_once(
        chat_list_controller,
        """            var selectedEntryId = !strongSelf.initializedFilters ? firstItemEntryId : strongSelf.chatListDisplayNode.mainContainerNode.currentItemFilter
            var resetCurrentEntry = false
""",
        """            var selectedEntryId = !strongSelf.initializedFilters ? firstItemEntryId : strongSelf.chatListDisplayNode.mainContainerNode.currentItemFilter
            if !strongSelf.initializedFilters, UserDefaults.standard.bool(forKey: "nagramix.openLastChatFolder") {
                let key = "nagramix.lastChatFolder.\\(strongSelf.context.account.peerId.toInt64())"
                if let storedId = UserDefaults.standard.object(forKey: key) as? NSNumber {
                    let restoredId: ChatListFilterTabEntryId = .filter(storedId.int32Value)
                    if resolvedItems.contains(where: { $0.id == restoredId }) {
                        selectedEntryId = restoredId
                    }
                }
            }
            var resetCurrentEntry = false
""",
        "restore last chat folder per account",
    )
    replace_once(
        chat_list_controller,
        """                } else {
                    selectedEntryId = .all
                }
            }
            let filtersLimit = isPremium == false ? limits.maxFoldersCount : nil
""",
        """                } else {
                    selectedEntryId = .all
                }
            }
            if !resolvedItems.contains(where: { $0.id == selectedEntryId }), let firstResolvedItem = resolvedItems.first {
                selectedEntryId = firstResolvedItem.id
            }
            let filtersLimit = isPremium == false ? limits.maxFoldersCount : nil
""",
        "safe fallback for hidden All Chats folder",
    )
    replace_once(
        chat_list_controller,
        """                    case .allChats:
                        hasAllChats = true
                        if let isPremium = isPremium, !isPremium && availableFilters.count > 0 {
""",
        """                    case .allChats:
                        hasAllChats = true
                        if UserDefaults.standard.bool(forKey: "nagramix.hideAllChatsFolder"), items.contains(where: { item in
                            if case .filter = item.0 {
                                return true
                            }
                            return false
                        }) {
                            break
                        }
                        if let isPremium = isPremium, !isPremium && availableFilters.count > 0 {
""",
        "remove All Chats from available filters",
    )
    replace_once(
        chat_list_controller_node,
        """        self.currentItemStateValue.set(itemNode.listNode.state |> map { state in
            let filterId: Int32?
""",
        """        if UserDefaults.standard.bool(forKey: "nagramix.openLastChatFolder") {
            let key = "nagramix.lastChatFolder.\\(self.context.account.peerId.toInt64())"
            switch id {
            case .all:
                UserDefaults.standard.removeObject(forKey: key)
            case let .filter(filterId):
                UserDefaults.standard.set(filterId, forKey: key)
            }
        }
        self.currentItemStateValue.set(itemNode.listNode.state |> map { state in
            let filterId: Int32?
""",
        "persist last chat folder per account",
    )

    chat_list_node = source / "submodules" / "ChatListUI" / "Sources" / "Node" / "ChatListNode.swift"
    replace_once(
        chat_list_node,
        """    public var hiddenPsaPeerId: EnginePeer.Id?\n    public var foundPeers: [(EnginePeer, EnginePeer?)]\n""",
        """    public var hiddenPsaPeerId: EnginePeer.Id?\n    public var showProxySponsor: Bool\n    public var foundPeers: [(EnginePeer, EnginePeer?)]\n""",
        "proxy sponsor state property",
    )
    replace_once(
        chat_list_node,
        """        hiddenPsaPeerId: EnginePeer.Id?,\n        selectedThreadIds: Set<Int64>,\n""",
        """        hiddenPsaPeerId: EnginePeer.Id?,\n        showProxySponsor: Bool,\n        selectedThreadIds: Set<Int64>,\n""",
        "proxy sponsor state initializer parameter",
    )
    replace_once(
        chat_list_node,
        """        self.hiddenPsaPeerId = hiddenPsaPeerId\n        self.selectedThreadIds = selectedThreadIds\n""",
        """        self.hiddenPsaPeerId = hiddenPsaPeerId\n        self.showProxySponsor = showProxySponsor\n        self.selectedThreadIds = selectedThreadIds\n""",
        "proxy sponsor state initializer assignment",
    )
    replace_once(
        chat_list_node,
        """        if lhs.hiddenPsaPeerId != rhs.hiddenPsaPeerId {\n            return false\n        }\n        if lhs.selectedThreadIds != rhs.selectedThreadIds {\n""",
        """        if lhs.hiddenPsaPeerId != rhs.hiddenPsaPeerId {\n            return false\n        }\n        if lhs.showProxySponsor != rhs.showProxySponsor {\n            return false\n        }\n        if lhs.selectedThreadIds != rhs.selectedThreadIds {\n""",
        "proxy sponsor state equality",
    )
    replace_once(
        chat_list_node,
        """    private let statePromise: ValuePromise<ChatListNodeState>\n    public var state: Signal<ChatListNodeState, NoError> {\n""",
        """    private let statePromise: ValuePromise<ChatListNodeState>\n    private var nagramixPreferencesObserver: NSObjectProtocol?\n    public var state: Signal<ChatListNodeState, NoError> {\n""",
        "proxy sponsor preferences observer property",
    )
    replace_once(
        chat_list_node,
        """hiddenItemShouldBeTemporaryRevealed: false, hiddenPsaPeerId: nil, selectedThreadIds: Set(), archiveStoryState: nil)\n""",
        """hiddenItemShouldBeTemporaryRevealed: false, hiddenPsaPeerId: nil, showProxySponsor: UserDefaults.standard.bool(forKey: "nagramix.showProxySponsor"), selectedThreadIds: Set(), archiveStoryState: nil)\n""",
        "proxy sponsor initial visibility",
    )
    replace_once(
        chat_list_node,
        """        super.init()\n        \n        if case .internal = context.sharedContext.applicationBindings.appBuildType {\n""",
        """        super.init()\n+        \n+        self.nagramixPreferencesObserver = NotificationCenter.default.addObserver(forName: Notification.Name("NagramiXPreferencesChanged"), object: nil, queue: .main, using: { [weak self] _ in\n+            self?.updateState { state in\n+                var state = state\n+                state.showProxySponsor = UserDefaults.standard.bool(forKey: "nagramix.showProxySponsor")\n+                return state\n+            }\n+        })\n+        \n+        if case .internal = context.sharedContext.applicationBindings.appBuildType {\n""",
        "proxy sponsor preferences observer setup",
    )
    replace_once(
        chat_list_node,
        """        self.updateIsMainTabDisposable?.dispose()\n    }\n""",
        """        self.updateIsMainTabDisposable?.dispose()\n+        if let nagramixPreferencesObserver = self.nagramixPreferencesObserver {\n+            NotificationCenter.default.removeObserver(nagramixPreferencesObserver)\n+        }\n+    }\n""",
        "proxy sponsor preferences observer cleanup",
    )

    chat_list_entries = source / "submodules" / "ChatListUI" / "Sources" / "Node" / "ChatListNodeEntries.swift"
    replace_once(
        chat_list_entries,
        """    let filteredAdditionalItemEntries = view.additionalItems.filter { item -> Bool in\n        return item.item.renderedPeer.peerId != state.hiddenPsaPeerId\n    }\n""",
        """    let filteredAdditionalItemEntries = view.additionalItems.filter { item -> Bool in\n        if item.item.renderedPeer.peerId == state.hiddenPsaPeerId {\n            return false\n        }\n        if case .proxy = item.promoInfo.content {\n            return state.showProxySponsor\n        }\n        return true\n    }\n""",
        "hide proxy sponsor by default",
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
    replace_once(
        peer_profile_items,
        """    if UserDefaults.standard.bool(forKey: "nagramix.showPeerIds"), let peer = data.peer {
        items[currentPeerInfoSection]!.append(PeerInfoScreenLabeledValueItem(id: 900, label: "ID", text: "\\(peer.id.toInt64())", textColor: .accent, action: { _, _ in
            UIPasteboard.general.string = "\\(peer.id.toInt64())"
        }, requestLayout: { animated in
            interaction.requestLayout(animated)
        }))
        if let resource = peer.profileImageRepresentations.first?.resource as? CloudPeerPhotoSizeMediaResource {
            items[currentPeerInfoSection]!.append(PeerInfoScreenLabeledValueItem(id: 901, label: "DC", text: "\\(resource.datacenterId)", textColor: .accent, action: nil, requestLayout: { animated in
                interaction.requestLayout(animated)
            }))
        }
    }
""",
        """    if UserDefaults.standard.bool(forKey: "nagramix.showPeerIds"), let peer = data.peer {
        items[currentPeerInfoSection]!.append(PeerInfoScreenLabeledValueItem(id: 900, label: "ID", text: "\\(peer.id.toInt64())", textColor: .accent, action: { _, _ in
            UIPasteboard.general.string = "\\(peer.id.toInt64())"
        }, requestLayout: { animated in
            interaction.requestLayout(animated)
        }))
        if let resource = peer.profileImageRepresentations.first?.resource as? CloudPeerPhotoSizeMediaResource {
            items[currentPeerInfoSection]!.append(PeerInfoScreenLabeledValueItem(id: 901, label: "DC", text: "\\(resource.datacenterId)", textColor: .accent, action: nil, requestLayout: { animated in
                interaction.requestLayout(animated)
            }))
        }
    }
    if UserDefaults.standard.bool(forKey: "nagramix.showChatCreationDate"), let peer = data.peer {
        let creationDate: Int32?
        switch peer {
        case let .channel(channel):
            creationDate = channel.creationDate
        case let .legacyGroup(group):
            creationDate = group.creationDate
        default:
            creationDate = nil
        }
        if let creationDate, creationDate > 0 {
            let dateText = stringForMediumDate(timestamp: creationDate, strings: presentationData.strings, dateTimeFormat: presentationData.dateTimeFormat, withTime: false)
            items[currentPeerInfoSection]!.append(PeerInfoScreenLabeledValueItem(id: 902, label: "Дата создания", text: dateText, textColor: .accent, action: nil, requestLayout: { animated in
                interaction.requestLayout(animated)
            }))
        }
    }
""",
        "exact group and channel creation date",
    )

    video_message_camera = source / "submodules" / "TelegramUI" / "Components" / "VideoMessageCameraScreen" / "Sources" / "VideoMessageCameraScreen.swift"
    replace_once(
        video_message_camera,
        """            let isDualCameraEnabled = Camera.isDualCameraSupported(forRoundVideo: true)\n            let isFrontPosition = "".isEmpty\n""",
        """            let isDualCameraEnabled = Camera.isDualCameraSupported(forRoundVideo: true)\n+            let preferBackCamera = UserDefaults.standard.object(forKey: "nagramix.preferBackCamera") == nil || UserDefaults.standard.bool(forKey: "nagramix.preferBackCamera")\n+            let isFrontPosition = !preferBackCamera\n""",
        "video message default camera",
    )

    call_manager = source / "submodules" / "TelegramCallsUI" / "Sources" / "PresentationCallManager.swift"
    replace_exact_count(
        call_manager,
        "enableTCP: experimentalSettings.enableVoipTcp,",
        "enableTCP: experimentalSettings.enableVoipTcp || UserDefaults.standard.bool(forKey: \"nagramix.forceTcpCalls\"),",
        3,
        "force TCP for VoIP calls",
    )

    chat_text_input_panel = source / "submodules" / "TelegramUI" / "Components" / "Chat" / "ChatTextInputPanelNode" / "Sources" / "ChatTextInputPanelNode.swift"
    replace_once(
        chat_text_input_panel,
        """    public func chatInputTextNodeShouldReturn(modifierFlags: UIKeyModifierFlags) -> Bool {
        var shouldSendMessage = false
""",
        """    public func chatInputTextNodeShouldReturn(modifierFlags: UIKeyModifierFlags) -> Bool {
        if !UserDefaults.standard.bool(forKey: "nagramix.sendWithEnter") || modifierFlags.contains(.shift) {
            return true
        }
        var shouldSendMessage = false
""",
        "send message with hardware Enter",
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
    replace_once(
        context_menus,
        """                let isRussian = chatPresentationInterfaceState.strings.baseLanguageCode == "ru"
                actions.append(.action(ContextMenuActionItem(text: isRussian ? "Переслать" : "Forward without Author", icon: { theme in
""",
        """                let isRussian = chatPresentationInterfaceState.strings.baseLanguageCode == "ru"
                if UserDefaults.standard.object(forKey: "nagramix.contextForwardWithoutAuthor") == nil || UserDefaults.standard.bool(forKey: "nagramix.contextForwardWithoutAuthor") {
                    actions.append(.action(ContextMenuActionItem(text: isRussian ? "Переслать" : "Forward without Author", icon: { theme in
""",
        "forward without author setting",
    )
    replace_once(
        context_menus,
        """                    f(.dismissWithoutContent)
                })))
                actions.append(.action(ContextMenuActionItem(text: isRussian ? "Переслать от" : "Forward with Author", icon: { theme in
""",
        """                    f(.dismissWithoutContent)
                    })))
                }
                if UserDefaults.standard.object(forKey: "nagramix.contextForwardWithAuthor") == nil || UserDefaults.standard.bool(forKey: "nagramix.contextForwardWithAuthor") {
                    actions.append(.action(ContextMenuActionItem(text: isRussian ? "Переслать от" : "Forward with Author", icon: { theme in
""",
        "forward with author setting",
    )
    replace_once(
        context_menus,
        """                    UserDefaults.standard.removeObject(forKey: "nagramix.forwardHideNamesOnce")
                    interfaceInteraction.forwardMessages(selectAll || isImage ? messages : [message])
                    f(.dismissWithoutContent)
                })))
                actions.append(.action(ContextMenuActionItem(text: isRussian ? "Сохранить в Избранное" : "Save to Saved Messages", icon: { theme in
""",
        """                    UserDefaults.standard.removeObject(forKey: "nagramix.forwardHideNamesOnce")
                    interfaceInteraction.forwardMessages(selectAll || isImage ? messages : [message])
                    f(.dismissWithoutContent)
                    })))
                }
                if UserDefaults.standard.object(forKey: "nagramix.contextSaveToSaved") == nil || UserDefaults.standard.bool(forKey: "nagramix.contextSaveToSaved") {
                    actions.append(.action(ContextMenuActionItem(text: isRussian ? "Сохранить в Избранное" : "Save to Saved Messages", icon: { theme in
""",
        "save to saved messages setting",
    )
    replace_once(
        context_menus,
        """                    controllerInteraction.displayUndo(.forward(savedMessages: true, text: chatPresentationInterfaceState.strings.Conversation_ForwardTooltip_SavedMessages_One))
                    f(.dismissWithoutContent)
                })))
            }
        }
""",
        """                    controllerInteraction.displayUndo(.forward(savedMessages: true, text: chatPresentationInterfaceState.strings.Conversation_ForwardTooltip_SavedMessages_One))
                    f(.dismissWithoutContent)
                    })))
                }
            }
        }
""",
        "close save to saved messages setting",
    )
    replace_once(
        context_menus,
        """            if hasSavableAttachment {
                actions.append(.action(ContextMenuActionItem(text: chatPresentationInterfaceState.strings.baseLanguageCode == "ru" ? "Сохранить в Файлы" : "Save to Files", icon: { theme in
""",
        """            if hasSavableAttachment && (UserDefaults.standard.object(forKey: "nagramix.contextSaveToFiles") == nil || UserDefaults.standard.bool(forKey: "nagramix.contextSaveToFiles")) {
                actions.append(.action(ContextMenuActionItem(text: chatPresentationInterfaceState.strings.baseLanguageCode == "ru" ? "Сохранить в Файлы" : "Save to Files", icon: { theme in
""",
        "save to files setting",
    )
    replace_once(
        context_menus,
        """                if let authorId = message.author?.id {
                    actions.append(.action(ContextMenuActionItem(text: chatPresentationInterfaceState.strings.baseLanguageCode == "ru" ? "Выбрать от" : "Select from Author", icon: { theme in
""",
        """                if (UserDefaults.standard.object(forKey: "nagramix.contextSelectFromAuthor") == nil || UserDefaults.standard.bool(forKey: "nagramix.contextSelectFromAuthor")), let authorId = message.author?.id {
                    actions.append(.action(ContextMenuActionItem(text: chatPresentationInterfaceState.strings.baseLanguageCode == "ru" ? "Выбрать от" : "Select from Author", icon: { theme in
""",
        "select from author setting",
    )
    replace_once(
        context_menus,
        """                if canTranslate {
                    actions.append(.action(ContextMenuActionItem(text: chatPresentationInterfaceState.strings.Conversation_ContextMenuTranslate, icon: { theme in
""",
        """                if canTranslate && (UserDefaults.standard.object(forKey: "nagramix.quickTranslate") == nil || UserDefaults.standard.bool(forKey: "nagramix.quickTranslate")) {
                    actions.append(.action(ContextMenuActionItem(text: chatPresentationInterfaceState.strings.Conversation_ContextMenuTranslate, icon: { theme in
""",
        "quick translate setting",
    )

    print("Applied NagramiX feature overlay, including Russian Debug UI")
