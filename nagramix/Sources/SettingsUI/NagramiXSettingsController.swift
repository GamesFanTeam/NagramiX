import Foundation
import UIKit
import Display
import SwiftSignalKit
import TelegramPresentationData
import PresentationDataUtils
import ItemListUI
import AccountContext
import NagramiXCore

private final class NagramiXSettingsControllerArguments {
    let updateHideContacts: (Bool) -> Void
    let updateHideCalls: (Bool) -> Void
    let updateHideTitles: (Bool) -> Void
    let updateShowSearchButton: (Bool) -> Void

    init(
        updateHideContacts: @escaping (Bool) -> Void,
        updateHideCalls: @escaping (Bool) -> Void,
        updateHideTitles: @escaping (Bool) -> Void,
        updateShowSearchButton: @escaping (Bool) -> Void
    ) {
        self.updateHideContacts = updateHideContacts
        self.updateHideCalls = updateHideCalls
        self.updateHideTitles = updateHideTitles
        self.updateShowSearchButton = updateShowSearchButton
    }
}

private enum NagramiXSettingsSection: Int32 {
    case tabs
}

private enum NagramiXSettingsEntry: ItemListNodeEntry {
    case tabsHeader
    case hideContacts(Bool)
    case hideCalls(Bool)
    case hideTitles(Bool)
    case showSearchButton(Bool)

    var section: ItemListSectionId {
        return NagramiXSettingsSection.tabs.rawValue
    }

    var stableId: Int32 {
        switch self {
        case .tabsHeader:
            return 0
        case .hideContacts:
            return 1
        case .hideCalls:
            return 2
        case .hideTitles:
            return 3
        case .showSearchButton:
            return 4
        }
    }

    static func < (lhs: NagramiXSettingsEntry, rhs: NagramiXSettingsEntry) -> Bool {
        return lhs.stableId < rhs.stableId
    }

    func item(presentationData: ItemListPresentationData, arguments: Any) -> ListViewItem {
        let arguments = arguments as! NagramiXSettingsControllerArguments
        switch self {
        case .tabsHeader:
            return ItemListSectionHeaderItem(presentationData: presentationData, text: "ПАНЕЛЬ ВКЛАДОК", sectionId: self.section)
        case let .hideContacts(value):
            return ItemListSwitchItem(presentationData: presentationData, systemStyle: .glass, title: "Скрыть вкладку «Контакты»", value: value, sectionId: self.section, style: .blocks, updated: arguments.updateHideContacts)
        case let .hideCalls(value):
            return ItemListSwitchItem(presentationData: presentationData, systemStyle: .glass, title: "Скрыть вкладку «Звонки»", value: value, sectionId: self.section, style: .blocks, updated: arguments.updateHideCalls)
        case let .hideTitles(value):
            return ItemListSwitchItem(presentationData: presentationData, systemStyle: .glass, title: "Скрыть имена вкладок", value: value, sectionId: self.section, style: .blocks, updated: arguments.updateHideTitles)
        case let .showSearchButton(value):
            return ItemListSwitchItem(presentationData: presentationData, systemStyle: .glass, title: "Показывать кнопку поиска", value: value, sectionId: self.section, style: .blocks, updated: arguments.updateShowSearchButton)
        }
    }
}

private func nagramiXSettingsEntries(settings: NagramiXTabSettings) -> [NagramiXSettingsEntry] {
    return [
        .tabsHeader,
        .hideContacts(settings.hideContacts),
        .hideCalls(settings.hideCalls),
        .hideTitles(settings.hideTitles),
        .showSearchButton(settings.showSearchButton),
    ]
}

public func nagramiXSettingsController(context: AccountContext) -> ViewController {
    let settingsPromise = ValuePromise(NagramiXTabSettings.current, ignoreRepeated: true)

    let update: ((inout NagramiXTabSettings) -> Void) -> Void = { transform in
        NagramiXTabSettings.update(transform)
        settingsPromise.set(NagramiXTabSettings.current)
    }

    let arguments = NagramiXSettingsControllerArguments(
        updateHideContacts: { value in
            update { $0.hideContacts = value }
        },
        updateHideCalls: { value in
            update { $0.hideCalls = value }
        },
        updateHideTitles: { value in
            update { $0.hideTitles = value }
        },
        updateShowSearchButton: { value in
            update { $0.showSearchButton = value }
        }
    )

    let signal = combineLatest(queue: .mainQueue(), context.sharedContext.presentationData, settingsPromise.get())
    |> map { presentationData, settings -> (ItemListControllerState, (ItemListNodeState, Any)) in
        var presentationData = presentationData
        presentationData = presentationData.withUpdated(theme: presentationData.theme.withModalBlocksBackground())

        let controllerState = ItemListControllerState(
            presentationData: ItemListPresentationData(presentationData),
            title: .text("Настройки NagramiX"),
            leftNavigationButton: nil,
            rightNavigationButton: nil,
            backNavigationButton: ItemListBackButton(title: presentationData.strings.Common_Back)
        )
        let listState = ItemListNodeState(
            presentationData: ItemListPresentationData(presentationData),
            entries: nagramiXSettingsEntries(settings: settings),
            style: .blocks,
            animateChanges: true
        )
        return (controllerState, (listState, arguments))
    }

    return ItemListController(context: context, state: signal)
}
