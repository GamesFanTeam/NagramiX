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
        """        return ProxySettings(enabled: false, servers: [], activeServer: nil, useForCalls: false, autoSwitchEnabled: false, autoSwitchInterval: 10)\n""",
        "proxy defaults",
    )
    replace_once(
        model,
        """    public init(enabled: Bool, servers: [ProxyServerSettings], activeServer: ProxyServerSettings?, useForCalls: Bool) {\n        self.enabled = enabled\n        self.servers = servers\n        self.activeServer = activeServer\n        self.useForCalls = useForCalls\n    }\n""",
        """    public init(enabled: Bool, servers: [ProxyServerSettings], activeServer: ProxyServerSettings?, useForCalls: Bool, autoSwitchEnabled: Bool = false, autoSwitchInterval: Int32 = 10) {\n        self.enabled = enabled\n        self.servers = servers\n        self.activeServer = activeServer\n        self.useForCalls = useForCalls\n        self.autoSwitchEnabled = autoSwitchEnabled\n        self.autoSwitchInterval = autoSwitchInterval\n    }\n""",
        "proxy initializer",
    )
    replace_once(
        model,
        """        self.useForCalls = ((try? container.decode(Int32.self, forKey: \"useForCalls\")) ?? 0) != 0\n""",
        """        self.useForCalls = ((try? container.decode(Int32.self, forKey: \"useForCalls\")) ?? 0) != 0\n        self.autoSwitchEnabled = ((try? container.decode(Int32.self, forKey: \"nagramixAutoSwitchEnabled\")) ?? 0) != 0\n        let decodedInterval = (try? container.decode(Int32.self, forKey: \"nagramixAutoSwitchInterval\")) ?? 10\n        self.autoSwitchInterval = [5, 10, 15, 30, 60].contains(decodedInterval) ? decodedInterval : 10\n""",
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
        """    public var validatedAutoSwitchInterval: Double {\n        return Double([5, 10, 15, 30, 60].contains(self.autoSwitchInterval) ? self.autoSwitchInterval : 10)\n    }\n\n    public var effectiveActiveServer: ProxyServerSettings? {\n""",
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
        """    }, toggleAutoSwitch: { value in\n        let _ = updateProxySettingsInteractively(accountManager: accountManager, { current in\n            var current = current\n            current.autoSwitchEnabled = value && current.servers.count > 1\n            return current\n        }).start()\n    }, selectNextAutoSwitchInterval: {\n        let _ = updateProxySettingsInteractively(accountManager: accountManager, { current in\n            var current = current\n            let values: [Int32] = [5, 10, 15, 30, 60]\n            let index = values.firstIndex(of: current.autoSwitchInterval) ?? 1\n            current.autoSwitchInterval = values[(index + 1) % values.count]\n            return current\n        }).start()\n    }, shareProxyList: {\n""",
        "proxy UI actions",
    )

    print("Applied NagramiX 0.1.2 proxy auto-switch feature overlay")
