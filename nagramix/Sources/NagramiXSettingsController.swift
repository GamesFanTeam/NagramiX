import Foundation
import UIKit
import Display
import SwiftSignalKit
import TelegramPresentationData
import ItemListUI
import AccountContext

private final class NagramiXSettingsControllerArguments {
    let openProxy: () -> Void
    let openAppIcons: () -> Void

    init(openProxy: @escaping () -> Void, openAppIcons: @escaping () -> Void) {
        self.openProxy = openProxy
        self.openAppIcons = openAppIcons
    }
}

private enum NagramiXSettingsSection: Int32 {
    case features
    case information
}

private enum NagramiXSettingsEntry: ItemListNodeEntry {
    case featuresHeader(String)
    case proxy(String)
    case appIcons(String)
    case information(String)

    var section: ItemListSectionId {
        switch self {
        case .featuresHeader, .proxy, .appIcons:
            return NagramiXSettingsSection.features.rawValue
        case .information:
            return NagramiXSettingsSection.information.rawValue
        }
    }

    var stableId: Int32 {
        switch self {
        case .featuresHeader:
            return 0
        case .proxy:
            return 1
        case .appIcons:
            return 2
        case .information:
            return 3
        }
    }

    static func < (lhs: NagramiXSettingsEntry, rhs: NagramiXSettingsEntry) -> Bool {
        return lhs.stableId < rhs.stableId
    }

    func item(presentationData: ItemListPresentationData, arguments: Any) -> ListViewItem {
        let arguments = arguments as! NagramiXSettingsControllerArguments
        switch self {
        case let .featuresHeader(text):
            return ItemListSectionHeaderItem(presentationData: presentationData, text: text, sectionId: self.section)
        case let .proxy(text):
            return ItemListDisclosureItem(presentationData: presentationData, systemStyle: .glass, icon: nil, title: text, label: "", sectionId: self.section, style: .blocks, action: {
                arguments.openProxy()
            })
        case let .appIcons(text):
            return ItemListDisclosureItem(presentationData: presentationData, systemStyle: .glass, icon: nil, title: text, label: "", sectionId: self.section, style: .blocks, action: {
                arguments.openAppIcons()
            })
        case let .information(text):
            return ItemListTextItem(presentationData: presentationData, text: .plain(text), sectionId: self.section)
        }
    }
}

private func nagramixSettingsEntries(presentationData: PresentationData) -> [NagramiXSettingsEntry] {
    let isRussian = presentationData.strings.baseLanguageCode == "ru"
    return [
        .featuresHeader(isRussian ? "РАБОЧИЕ ФУНКЦИИ" : "AVAILABLE FEATURES"),
        .proxy(isRussian ? "Прокси и автопереключение" : "Proxy and Auto Switch"),
        .appIcons(isRussian ? "Иконки приложения" : "App Icons"),
        .information(isRussian
            ? "На этом экране находятся только функции NagramiX, которые действительно подключены к поведению приложения.\nНовые группы твиков будут появляться здесь по мере реализации и проверки.\nПустые или декоративные переключатели не добавляются."
            : "This screen contains only NagramiX features that are connected to real application behavior.\nNew tweak groups will appear here after implementation and validation.\nEmpty or decorative switches are not added."),
    ]
}

public func nagramiXSettingsController(context: AccountContext) -> ViewController {
    var pushControllerImpl: ((ViewController) -> Void)?
    let arguments = NagramiXSettingsControllerArguments(openProxy: {
        pushControllerImpl?(proxySettingsController(context: context))
    }, openAppIcons: {
        pushControllerImpl?(themeSettingsController(context: context, focusOnItemTag: .icon))
    })

    let signal = context.sharedContext.presentationData
    |> deliverOnMainQueue
    |> map { presentationData -> (ItemListControllerState, (ItemListNodeState, Any)) in
        var presentationData = presentationData
        presentationData = presentationData.withUpdated(theme: presentationData.theme.withModalBlocksBackground())
        let isRussian = presentationData.strings.baseLanguageCode == "ru"
        let controllerState = ItemListControllerState(
            presentationData: ItemListPresentationData(presentationData),
            title: .text(isRussian ? "Настройки NagramiX" : "NagramiX Settings"),
            leftNavigationButton: nil,
            rightNavigationButton: nil,
            backNavigationButton: ItemListBackButton(title: presentationData.strings.Common_Back)
        )
        let listState = ItemListNodeState(
            presentationData: ItemListPresentationData(presentationData),
            entries: nagramixSettingsEntries(presentationData: presentationData),
            style: .blocks,
            animateChanges: false
        )
        return (controllerState, (listState, arguments))
    }

    let controller = ItemListController(context: context, state: signal)
    pushControllerImpl = { [weak controller] nextController in
        controller?.push(nextController)
    }
    return controller
}
