import Foundation
import UIKit
import Display
import SwiftSignalKit
import TelegramPresentationData
import PresentationDataUtils
import ItemListUI
import AccountContext
import NagramiXCore

private final class NagramiXSettingsControllerHolder {
    weak var controller: ViewController?
    weak var restartActionSheet: ActionSheetController?
}

private final class NagramiXSettingsControllerArguments {
    let updateHideContacts: (Bool) -> Void
    let updateHideCalls: (Bool) -> Void
    let updateHideTitles: (Bool) -> Void
    let updateShowSearchButton: (Bool) -> Void
    let updateShowProxyButton: (Bool) -> Void
    let updateUseRearCameraForVideoMessages: (Bool) -> Void
    let updateHideStories: (Bool) -> Void
    let updateDisableStoryCameraSwipe: (Bool) -> Void
    let updateConfirmStoryViewing: (Bool) -> Void
    let updateEnableStoryRepost: (Bool) -> Void

    init(
        updateHideContacts: @escaping (Bool) -> Void,
        updateHideCalls: @escaping (Bool) -> Void,
        updateHideTitles: @escaping (Bool) -> Void,
        updateShowSearchButton: @escaping (Bool) -> Void,
        updateShowProxyButton: @escaping (Bool) -> Void,
        updateUseRearCameraForVideoMessages: @escaping (Bool) -> Void,
        updateHideStories: @escaping (Bool) -> Void,
        updateDisableStoryCameraSwipe: @escaping (Bool) -> Void,
        updateConfirmStoryViewing: @escaping (Bool) -> Void,
        updateEnableStoryRepost: @escaping (Bool) -> Void
    ) {
        self.updateHideContacts = updateHideContacts
        self.updateHideCalls = updateHideCalls
        self.updateHideTitles = updateHideTitles
        self.updateShowSearchButton = updateShowSearchButton
        self.updateShowProxyButton = updateShowProxyButton
        self.updateUseRearCameraForVideoMessages = updateUseRearCameraForVideoMessages
        self.updateHideStories = updateHideStories
        self.updateDisableStoryCameraSwipe = updateDisableStoryCameraSwipe
        self.updateConfirmStoryViewing = updateConfirmStoryViewing
        self.updateEnableStoryRepost = updateEnableStoryRepost
    }
}

private enum NagramiXSettingsSection: Int32 {
    case tabs
    case videoMessages
    case stories
}

private enum NagramiXSettingsEntry: ItemListNodeEntry {
    case tabsHeader
    case hideContacts(Bool)
    case hideCalls(Bool)
    case hideTitles(Bool)
    case showSearchButton(Bool)
    case showProxyButton(Bool)
    case videoMessagesHeader
    case useRearCameraForVideoMessages(Bool)
    case storiesHeader
    case hideStories(Bool)
    case disableStoryCameraSwipe(Bool)
    case confirmStoryViewing(Bool)
    case enableStoryRepost(Bool)

    var section: ItemListSectionId {
        switch self {
        case .tabsHeader, .hideContacts, .hideCalls, .hideTitles, .showSearchButton, .showProxyButton:
            return NagramiXSettingsSection.tabs.rawValue
        case .videoMessagesHeader, .useRearCameraForVideoMessages:
            return NagramiXSettingsSection.videoMessages.rawValue
        case .storiesHeader, .hideStories, .disableStoryCameraSwipe, .confirmStoryViewing, .enableStoryRepost:
            return NagramiXSettingsSection.stories.rawValue
        }
    }

    var stableId: Int32 {
        switch self {
        case .tabsHeader: return 0
        case .hideContacts: return 1
        case .hideCalls: return 2
        case .hideTitles: return 3
        case .showSearchButton: return 4
        case .showProxyButton: return 5
        case .videoMessagesHeader: return 10
        case .useRearCameraForVideoMessages: return 11
        case .storiesHeader: return 20
        case .hideStories: return 21
        case .disableStoryCameraSwipe: return 22
        case .confirmStoryViewing: return 23
        case .enableStoryRepost: return 24
        }
    }

    static func < (lhs: NagramiXSettingsEntry, rhs: NagramiXSettingsEntry) -> Bool {
        return lhs.stableId < rhs.stableId
    }

    func item(presentationData: ItemListPresentationData, arguments: Any) -> ListViewItem {
        let arguments = arguments as! NagramiXSettingsControllerArguments
        switch self {
        case .tabsHeader:
            return ItemListSectionHeaderItem(presentationData: presentationData, text: presentationData.strings.nagramiXTabsHeader, sectionId: self.section)
        case let .hideContacts(value):
            return ItemListSwitchItem(presentationData: presentationData, systemStyle: .glass, title: presentationData.strings.nagramiXHideContactsTab, value: value, sectionId: self.section, style: .blocks, updated: arguments.updateHideContacts)
        case let .hideCalls(value):
            return ItemListSwitchItem(presentationData: presentationData, systemStyle: .glass, title: presentationData.strings.nagramiXHideCallsTab, value: value, sectionId: self.section, style: .blocks, updated: arguments.updateHideCalls)
        case let .hideTitles(value):
            return ItemListSwitchItem(presentationData: presentationData, systemStyle: .glass, title: presentationData.strings.nagramiXHideTabTitles, value: value, sectionId: self.section, style: .blocks, updated: arguments.updateHideTitles)
        case let .showSearchButton(value):
            return ItemListSwitchItem(presentationData: presentationData, systemStyle: .glass, title: presentationData.strings.nagramiXShowSearchButton, value: value, sectionId: self.section, style: .blocks, updated: arguments.updateShowSearchButton)
        case let .showProxyButton(value):
            return ItemListSwitchItem(presentationData: presentationData, systemStyle: .glass, title: presentationData.strings.nagramiXShowProxyButton, value: value, sectionId: self.section, style: .blocks, updated: arguments.updateShowProxyButton)
        case .videoMessagesHeader:
            return ItemListSectionHeaderItem(presentationData: presentationData, text: presentationData.strings.nagramiXVideoMessagesHeader, sectionId: self.section)
        case let .useRearCameraForVideoMessages(value):
            return ItemListSwitchItem(presentationData: presentationData, systemStyle: .glass, title: presentationData.strings.nagramiXUseRearCamera, value: value, sectionId: self.section, style: .blocks, updated: arguments.updateUseRearCameraForVideoMessages)
        case .storiesHeader:
            return ItemListSectionHeaderItem(presentationData: presentationData, text: presentationData.strings.nagramiXStoriesHeader, sectionId: self.section)
        case let .hideStories(value):
            return ItemListSwitchItem(presentationData: presentationData, systemStyle: .glass, title: presentationData.strings.nagramiXHideStories, value: value, sectionId: self.section, style: .blocks, updated: arguments.updateHideStories)
        case let .disableStoryCameraSwipe(value):
            return ItemListSwitchItem(presentationData: presentationData, systemStyle: .glass, title: presentationData.strings.nagramiXDisableStoryCameraSwipe, value: value, sectionId: self.section, style: .blocks, updated: arguments.updateDisableStoryCameraSwipe)
        case let .confirmStoryViewing(value):
            return ItemListSwitchItem(presentationData: presentationData, systemStyle: .glass, title: presentationData.strings.nagramiXConfirmStoryViewing, value: value, sectionId: self.section, style: .blocks, updated: arguments.updateConfirmStoryViewing)
        case let .enableStoryRepost(value):
            return ItemListSwitchItem(presentationData: presentationData, systemStyle: .glass, title: presentationData.strings.nagramiXEnableStoryRepost, value: value, sectionId: self.section, style: .blocks, updated: arguments.updateEnableStoryRepost)
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
        .showProxyButton(settings.showProxyButton),
        .videoMessagesHeader,
        .useRearCameraForVideoMessages(settings.useRearCameraForVideoMessages),
        .storiesHeader,
        .hideStories(settings.hideStories),
        .disableStoryCameraSwipe(settings.disableStoryCameraSwipe),
        .confirmStoryViewing(settings.confirmStoryViewing),
        .enableStoryRepost(settings.enableStoryRepost),
    ]
}

public func nagramiXSettingsController(context: AccountContext) -> ViewController {
    let settingsPromise = ValuePromise(NagramiXTabSettings.current, ignoreRepeated: false)
    let controllerHolder = NagramiXSettingsControllerHolder()

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
            guard controllerHolder.restartActionSheet == nil else {
                settingsPromise.set(NagramiXTabSettings.current)
                return
            }

            var pendingSettings = NagramiXTabSettings.current
            pendingSettings.hideTitles = value
            settingsPromise.set(pendingSettings)

            let presentationData = context.sharedContext.currentPresentationData.with { $0 }
            let actionSheet = ActionSheetController(presentationData: presentationData)
            controllerHolder.restartActionSheet = actionSheet
            var didApply = false
            actionSheet.dismissed = { _ in
                controllerHolder.restartActionSheet = nil
                if !didApply {
                    settingsPromise.set(NagramiXTabSettings.current)
                }
            }
            actionSheet.setItemGroups([
                ActionSheetItemGroup(items: [
                    ActionSheetTextItem(title: presentationData.strings.nagramiXRestartRequiredTitle + "\n" + presentationData.strings.nagramiXRestartRequiredText),
                    ActionSheetButtonItem(title: presentationData.strings.nagramiXRestartAction, color: .accent, font: .bold, action: { [weak actionSheet] in
                        didApply = true
                        actionSheet?.dismissAnimated()
                        update { $0.hideTitles = value }
                        NagramiXTabSettings.requestTabInterfaceSoftRestart()
                    }),
                ]),
                ActionSheetItemGroup(items: [
                    ActionSheetButtonItem(title: presentationData.strings.Common_Cancel, color: .accent, font: .bold, action: { [weak actionSheet] in
                        actionSheet?.dismissAnimated()
                        settingsPromise.set(NagramiXTabSettings.current)
                    }),
                ]),
            ])
            controllerHolder.controller?.present(actionSheet, in: .window(.root))
        },
        updateShowSearchButton: { value in
            update { $0.showSearchButton = value }
        },
        updateShowProxyButton: { value in
            update { $0.showProxyButton = value }
        },
        updateUseRearCameraForVideoMessages: { value in
            update { $0.useRearCameraForVideoMessages = value }
        },
        updateHideStories: { value in
            update { $0.hideStories = value }
        },
        updateDisableStoryCameraSwipe: { value in
            update { $0.disableStoryCameraSwipe = value }
        },
        updateConfirmStoryViewing: { value in
            update { $0.confirmStoryViewing = value }
        },
        updateEnableStoryRepost: { value in
            update { $0.enableStoryRepost = value }
        }
    )

    let signal = combineLatest(queue: .mainQueue(), context.sharedContext.presentationData, settingsPromise.get())
    |> map { presentationData, settings -> (ItemListControllerState, (ItemListNodeState, Any)) in
        var presentationData = presentationData
        presentationData = presentationData.withUpdated(theme: presentationData.theme.withModalBlocksBackground())

        let controllerState = ItemListControllerState(
            presentationData: ItemListPresentationData(presentationData),
            title: .text(presentationData.strings.nagramiXSettingsTitle),
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

    let controller = ItemListController(context: context, state: signal)
    controllerHolder.controller = controller
    return controller
}
