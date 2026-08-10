import Foundation
import UIKit
import Display
import SwiftSignalKit
import TelegramPresentationData
import ItemListUI
import AccountContext

private enum NagramiXPreferenceKey {
    static let hideTabBar = "nagramix.hideTabBar"
    static let showContactsTab = "nagramix.showContactsTab"
    static let showCallsTab = "nagramix.showCallsTab"
    static let showTabNames = "nagramix.showTabNames"
    static let showSearchButton = "nagramix.showSearchButton"
    static let hideAllChatsFolder = "nagramix.hideAllChatsFolder"
    static let openLastChatFolder = "nagramix.openLastChatFolder"
    static let showProxySponsor = "nagramix.showProxySponsor"
    static let hideStories = "nagramix.hideStories"
    static let disableStoryCameraSwipe = "nagramix.disableStoryCameraSwipe"
    static let quickTranslate = "nagramix.quickTranslate"
    static let sendWithEnter = "nagramix.sendWithEnter"
    static let forceTcpCalls = "nagramix.forceTcpCalls"
    static let contextForwardWithoutAuthor = "nagramix.contextForwardWithoutAuthor"
    static let contextForwardWithAuthor = "nagramix.contextForwardWithAuthor"
    static let contextSaveToSaved = "nagramix.contextSaveToSaved"
    static let contextSaveToFiles = "nagramix.contextSaveToFiles"
    static let contextSelectFromAuthor = "nagramix.contextSelectFromAuthor"
    static let showMessageSeconds = "nagramix.showMessageSeconds"
    static let confirmCalls = "nagramix.confirmCalls"
    static let hidePhoneNumber = "nagramix.hidePhoneNumber"
    static let showPeerIds = "nagramix.showPeerIds"
    static let showChatCreationDate = "nagramix.showChatCreationDate"
    static let preferBackCamera = "nagramix.preferBackCamera"
    static let compactChatList = "nagramix.compactChatList"
    static let compactMessagePreview = "nagramix.compactMessagePreview"
    static let changedNotification = Notification.Name("NagramiXPreferencesChanged")
}

private struct NagramiXLocalSettings: Equatable {
    var hideTabBar: Bool
    var showContactsTab: Bool
    var showCallsTab: Bool
    var showTabNames: Bool
    var showSearchButton: Bool
    var hideAllChatsFolder: Bool
    var openLastChatFolder: Bool
    var showProxySponsor: Bool
    var hideStories: Bool
    var disableStoryCameraSwipe: Bool
    var quickTranslate: Bool
    var sendWithEnter: Bool
    var forceTcpCalls: Bool
    var contextForwardWithoutAuthor: Bool
    var contextForwardWithAuthor: Bool
    var contextSaveToSaved: Bool
    var contextSaveToFiles: Bool
    var contextSelectFromAuthor: Bool
    var showMessageSeconds: Bool
    var confirmCalls: Bool
    var hidePhoneNumber: Bool
    var showPeerIds: Bool
    var showChatCreationDate: Bool
    var preferBackCamera: Bool
    var compactChatList: Bool
    var compactMessagePreview: Bool

    static func load() -> NagramiXLocalSettings {
        let defaults = UserDefaults.standard
        return NagramiXLocalSettings(
            hideTabBar: defaults.bool(forKey: NagramiXPreferenceKey.hideTabBar),
            showContactsTab: defaults.bool(forKey: NagramiXPreferenceKey.showContactsTab),
            showCallsTab: defaults.bool(forKey: NagramiXPreferenceKey.showCallsTab),
            showTabNames: defaults.object(forKey: NagramiXPreferenceKey.showTabNames) == nil ? true : defaults.bool(forKey: NagramiXPreferenceKey.showTabNames),
            showSearchButton: defaults.object(forKey: NagramiXPreferenceKey.showSearchButton) == nil ? true : defaults.bool(forKey: NagramiXPreferenceKey.showSearchButton),
            hideAllChatsFolder: defaults.bool(forKey: NagramiXPreferenceKey.hideAllChatsFolder),
            openLastChatFolder: defaults.bool(forKey: NagramiXPreferenceKey.openLastChatFolder),
            showProxySponsor: defaults.bool(forKey: NagramiXPreferenceKey.showProxySponsor),
            hideStories: defaults.bool(forKey: NagramiXPreferenceKey.hideStories),
            disableStoryCameraSwipe: defaults.bool(forKey: NagramiXPreferenceKey.disableStoryCameraSwipe),
            quickTranslate: defaults.object(forKey: NagramiXPreferenceKey.quickTranslate) == nil ? true : defaults.bool(forKey: NagramiXPreferenceKey.quickTranslate),
            sendWithEnter: defaults.bool(forKey: NagramiXPreferenceKey.sendWithEnter),
            forceTcpCalls: defaults.bool(forKey: NagramiXPreferenceKey.forceTcpCalls),
            contextForwardWithoutAuthor: defaults.object(forKey: NagramiXPreferenceKey.contextForwardWithoutAuthor) == nil ? true : defaults.bool(forKey: NagramiXPreferenceKey.contextForwardWithoutAuthor),
            contextForwardWithAuthor: defaults.object(forKey: NagramiXPreferenceKey.contextForwardWithAuthor) == nil ? true : defaults.bool(forKey: NagramiXPreferenceKey.contextForwardWithAuthor),
            contextSaveToSaved: defaults.object(forKey: NagramiXPreferenceKey.contextSaveToSaved) == nil ? true : defaults.bool(forKey: NagramiXPreferenceKey.contextSaveToSaved),
            contextSaveToFiles: defaults.object(forKey: NagramiXPreferenceKey.contextSaveToFiles) == nil ? true : defaults.bool(forKey: NagramiXPreferenceKey.contextSaveToFiles),
            contextSelectFromAuthor: defaults.object(forKey: NagramiXPreferenceKey.contextSelectFromAuthor) == nil ? true : defaults.bool(forKey: NagramiXPreferenceKey.contextSelectFromAuthor),
            showMessageSeconds: defaults.bool(forKey: NagramiXPreferenceKey.showMessageSeconds),
            confirmCalls: defaults.bool(forKey: NagramiXPreferenceKey.confirmCalls),
            hidePhoneNumber: defaults.bool(forKey: NagramiXPreferenceKey.hidePhoneNumber),
            showPeerIds: defaults.bool(forKey: NagramiXPreferenceKey.showPeerIds),
            showChatCreationDate: defaults.bool(forKey: NagramiXPreferenceKey.showChatCreationDate),
            preferBackCamera: defaults.object(forKey: NagramiXPreferenceKey.preferBackCamera) == nil ? true : defaults.bool(forKey: NagramiXPreferenceKey.preferBackCamera),
            compactChatList: defaults.bool(forKey: NagramiXPreferenceKey.compactChatList),
            compactMessagePreview: defaults.bool(forKey: NagramiXPreferenceKey.compactMessagePreview)
        )
    }
}

private final class NagramiXSettingsControllerArguments {
    let openProxy: () -> Void
    let openAppIcons: () -> Void
    let update: (WritableKeyPath<NagramiXLocalSettings, Bool>, String, Bool) -> Void

    init(
        openProxy: @escaping () -> Void,
        openAppIcons: @escaping () -> Void,
        update: @escaping (WritableKeyPath<NagramiXLocalSettings, Bool>, String, Bool) -> Void
    ) {
        self.openProxy = openProxy
        self.openAppIcons = openAppIcons
        self.update = update
    }
}

private enum NagramiXSettingsSection: Int32 {
    case navigation
    case folders
    case interface
    case stories
    case contextMenu
    case privacy
    case media
    case tools
    case information
}

private enum NagramiXSettingsEntry: ItemListNodeEntry {
    case header(Int32, String)
    case toggle(Int32, Int32, String, Bool, WritableKeyPath<NagramiXLocalSettings, Bool>, String)
    case proxy(String)
    case appIcons(String)
    case information(String)

    var section: ItemListSectionId {
        switch self {
        case let .header(section, _), let .toggle(section, _, _, _, _, _):
            return section
        case .proxy, .appIcons:
            return NagramiXSettingsSection.tools.rawValue
        case .information:
            return NagramiXSettingsSection.information.rawValue
        }
    }

    var stableId: Int32 {
        switch self {
        case let .header(section, _):
            return section * 100
        case let .toggle(section, index, _, _, _, _):
            return section * 100 + index
        case .proxy:
            return 790
        case .appIcons:
            return 791
        case .information:
            return 801
        }
    }

    static func < (lhs: NagramiXSettingsEntry, rhs: NagramiXSettingsEntry) -> Bool {
        return lhs.stableId < rhs.stableId
    }

    func item(presentationData: ItemListPresentationData, arguments: Any) -> ListViewItem {
        let arguments = arguments as! NagramiXSettingsControllerArguments
        switch self {
        case let .header(_, text):
            return ItemListSectionHeaderItem(presentationData: presentationData, text: text, sectionId: self.section)
        case let .toggle(_, _, text, value, keyPath, key):
            return ItemListSwitchItem(presentationData: presentationData, systemStyle: .glass, title: text, value: value, enableInteractiveChanges: true, enabled: true, sectionId: self.section, style: .blocks, updated: { value in
                arguments.update(keyPath, key, value)
            })
        case let .proxy(text):
            return ItemListDisclosureItem(presentationData: presentationData, systemStyle: .glass, icon: nil, title: text, label: "", sectionId: self.section, style: .blocks, action: {
                arguments.openProxy()
            })
        case let .appIcons(text):
            return ItemListDisclosureItem(presentationData: presentationData, systemStyle: .glass, icon: nil, title: text, label: "8", sectionId: self.section, style: .blocks, action: {
                arguments.openAppIcons()
            })
        case let .information(text):
            return ItemListTextItem(presentationData: presentationData, text: .plain(text), sectionId: self.section)
        }
    }
}

private func nagramixSettingsEntries(presentationData: PresentationData, settings: NagramiXLocalSettings) -> [NagramiXSettingsEntry] {
    let isRussian = presentationData.strings.baseLanguageCode == "ru"
    return [
        .header(NagramiXSettingsSection.navigation.rawValue, isRussian ? "НИЖНЯЯ ПАНЕЛЬ" : "TAB BAR"),
        .toggle(NagramiXSettingsSection.navigation.rawValue, 1, isRussian ? "Скрыть панель вкладок" : "Hide Tab Bar", settings.hideTabBar, \.hideTabBar, NagramiXPreferenceKey.hideTabBar),
        .toggle(NagramiXSettingsSection.navigation.rawValue, 2, isRussian ? "Показывать Контакты" : "Show Contacts", settings.showContactsTab, \.showContactsTab, NagramiXPreferenceKey.showContactsTab),
        .toggle(NagramiXSettingsSection.navigation.rawValue, 3, isRussian ? "Показывать Звонки" : "Show Calls", settings.showCallsTab, \.showCallsTab, NagramiXPreferenceKey.showCallsTab),
        .toggle(NagramiXSettingsSection.navigation.rawValue, 4, isRussian ? "Имена вкладок" : "Tab Names", settings.showTabNames, \.showTabNames, NagramiXPreferenceKey.showTabNames),
        .toggle(NagramiXSettingsSection.navigation.rawValue, 5, isRussian ? "Кнопка поиска" : "Search Button", settings.showSearchButton, \.showSearchButton, NagramiXPreferenceKey.showSearchButton),

        .header(NagramiXSettingsSection.folders.rawValue, isRussian ? "ПАПКИ С ЧАТАМИ" : "CHAT FOLDERS"),
        .toggle(NagramiXSettingsSection.folders.rawValue, 1, isRussian ? "Скрыть «Все чаты»" : "Hide All Chats", settings.hideAllChatsFolder, \.hideAllChatsFolder, NagramiXPreferenceKey.hideAllChatsFolder),
        .toggle(NagramiXSettingsSection.folders.rawValue, 2, isRussian ? "Открывать последнюю папку" : "Open Last Folder", settings.openLastChatFolder, \.openLastChatFolder, NagramiXPreferenceKey.openLastChatFolder),

        .header(NagramiXSettingsSection.interface.rawValue, isRussian ? "ЧАТЫ И СООБЩЕНИЯ" : "CHATS AND MESSAGES"),
        .toggle(NagramiXSettingsSection.interface.rawValue, 1, isRussian ? "Показывать секунды" : "Show Seconds", settings.showMessageSeconds, \.showMessageSeconds, NagramiXPreferenceKey.showMessageSeconds),
        .toggle(NagramiXSettingsSection.interface.rawValue, 2, isRussian ? "Компактный список чатов" : "Compact Chat List", settings.compactChatList, \.compactChatList, NagramiXPreferenceKey.compactChatList),
        .toggle(NagramiXSettingsSection.interface.rawValue, 3, isRussian ? "Компактный предпросмотр" : "Compact Message Preview", settings.compactMessagePreview, \.compactMessagePreview, NagramiXPreferenceKey.compactMessagePreview),
        .toggle(NagramiXSettingsSection.interface.rawValue, 4, isRussian ? "Отправка кнопкой «Ввод»" : "Send with Enter", settings.sendWithEnter, \.sendWithEnter, NagramiXPreferenceKey.sendWithEnter),

        .header(NagramiXSettingsSection.stories.rawValue, isRussian ? "ИСТОРИИ И ПЕРЕВОД" : "STORIES AND TRANSLATION"),
        .toggle(NagramiXSettingsSection.stories.rawValue, 1, isRussian ? "Скрыть истории" : "Hide Stories", settings.hideStories, \.hideStories, NagramiXPreferenceKey.hideStories),
        .toggle(NagramiXSettingsSection.stories.rawValue, 2, isRussian ? "Отключить свайп для записи истории" : "Disable Story Camera Swipe", settings.disableStoryCameraSwipe, \.disableStoryCameraSwipe, NagramiXPreferenceKey.disableStoryCameraSwipe),
        .toggle(NagramiXSettingsSection.stories.rawValue, 3, isRussian ? "Кнопка быстрого перевода" : "Quick Translate Action", settings.quickTranslate, \.quickTranslate, NagramiXPreferenceKey.quickTranslate),

        .header(NagramiXSettingsSection.contextMenu.rawValue, isRussian ? "КОНТЕКСТНОЕ МЕНЮ" : "CONTEXT MENU"),
        .toggle(NagramiXSettingsSection.contextMenu.rawValue, 1, isRussian ? "Переслать без автора" : "Forward without Author", settings.contextForwardWithoutAuthor, \.contextForwardWithoutAuthor, NagramiXPreferenceKey.contextForwardWithoutAuthor),
        .toggle(NagramiXSettingsSection.contextMenu.rawValue, 2, isRussian ? "Переслать от" : "Forward with Author", settings.contextForwardWithAuthor, \.contextForwardWithAuthor, NagramiXPreferenceKey.contextForwardWithAuthor),
        .toggle(NagramiXSettingsSection.contextMenu.rawValue, 3, isRussian ? "Сохранить в Избранное" : "Save to Saved Messages", settings.contextSaveToSaved, \.contextSaveToSaved, NagramiXPreferenceKey.contextSaveToSaved),
        .toggle(NagramiXSettingsSection.contextMenu.rawValue, 4, isRussian ? "Сохранить в Файлы" : "Save to Files", settings.contextSaveToFiles, \.contextSaveToFiles, NagramiXPreferenceKey.contextSaveToFiles),
        .toggle(NagramiXSettingsSection.contextMenu.rawValue, 5, isRussian ? "Выбрать от автора" : "Select from Author", settings.contextSelectFromAuthor, \.contextSelectFromAuthor, NagramiXPreferenceKey.contextSelectFromAuthor),

        .header(NagramiXSettingsSection.privacy.rawValue, isRussian ? "ПРОФИЛЬ И ЗВОНКИ" : "PROFILE AND CALLS"),
        .toggle(NagramiXSettingsSection.privacy.rawValue, 1, isRussian ? "Подтверждать вызовы" : "Confirm Calls", settings.confirmCalls, \.confirmCalls, NagramiXPreferenceKey.confirmCalls),
        .toggle(NagramiXSettingsSection.privacy.rawValue, 2, isRussian ? "Скрывать мой номер" : "Hide My Phone Number", settings.hidePhoneNumber, \.hidePhoneNumber, NagramiXPreferenceKey.hidePhoneNumber),
        .toggle(NagramiXSettingsSection.privacy.rawValue, 3, isRussian ? "Показывать ID профиля" : "Show Profile IDs", settings.showPeerIds, \.showPeerIds, NagramiXPreferenceKey.showPeerIds),
        .toggle(NagramiXSettingsSection.privacy.rawValue, 4, isRussian ? "Принудительно использовать TCP для звонков" : "Force TCP for Calls", settings.forceTcpCalls, \.forceTcpCalls, NagramiXPreferenceKey.forceTcpCalls),
        .toggle(NagramiXSettingsSection.privacy.rawValue, 5, isRussian ? "Показывать дату создания чата" : "Show Chat Creation Date", settings.showChatCreationDate, \.showChatCreationDate, NagramiXPreferenceKey.showChatCreationDate),

        .header(NagramiXSettingsSection.media.rawValue, isRussian ? "КАМЕРА" : "CAMERA"),
        .toggle(NagramiXSettingsSection.media.rawValue, 1, isRussian ? "Задняя камера для круглых видео" : "Back Camera for Video Messages", settings.preferBackCamera, \.preferBackCamera, NagramiXPreferenceKey.preferBackCamera),

        .header(NagramiXSettingsSection.tools.rawValue, isRussian ? "ИНСТРУМЕНТЫ" : "TOOLS"),
        .toggle(NagramiXSettingsSection.tools.rawValue, 1, isRussian ? "Показывать Спонсор Прокси" : "Show Proxy Sponsor", settings.showProxySponsor, \.showProxySponsor, NagramiXPreferenceKey.showProxySponsor),
        .proxy(isRussian ? "Прокси и автопереключение" : "Proxy and Auto Switch"),
        .appIcons(isRussian ? "Иконки приложения" : "App Icons"),

        .information(isRussian
            ? "Изменения интерфейса применяются сразу или после повторного открытия экрана.\nСпонсор Прокси по умолчанию скрыт.\nСкрытие номера действует только в интерфейсе NagramiX.\nНастройки конфиденциальности Telegram при этом не изменяются."
            : "Tab bar changes are applied immediately.\nProxy Sponsor is hidden by default.\nPhone number hiding only affects the NagramiX interface.\nTelegram privacy settings are not changed."),
    ]
}

public func nagramiXSettingsController(context: AccountContext) -> ViewController {
    var pushControllerImpl: ((ViewController) -> Void)?
    let settingsPromise = ValuePromise<NagramiXLocalSettings>(NagramiXLocalSettings.load(), ignoreRepeated: true)
    let settingsValue = Atomic(value: NagramiXLocalSettings.load())

    let arguments = NagramiXSettingsControllerArguments(openProxy: {
        pushControllerImpl?(proxySettingsController(context: context))
    }, openAppIcons: {
        pushControllerImpl?(themeSettingsController(context: context, focusOnItemTag: .icon))
    }, update: { keyPath, key, value in
        let updated = settingsValue.modify { current in
            var current = current
            current[keyPath: keyPath] = value
            return current
        }
        UserDefaults.standard.set(value, forKey: key)
        settingsPromise.set(updated)
        NotificationCenter.default.post(name: NagramiXPreferenceKey.changedNotification, object: nil)
    })

    let signal = combineLatest(context.sharedContext.presentationData, settingsPromise.get())
    |> deliverOnMainQueue
    |> map { presentationData, settings -> (ItemListControllerState, (ItemListNodeState, Any)) in
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
            entries: nagramixSettingsEntries(presentationData: presentationData, settings: settings),
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
