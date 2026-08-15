import Foundation

public struct NagramiXTabSettings: Equatable {
    public static let changedNotification = Notification.Name("NagramiXSettingsChanged")
    public static let softRestartRequestedNotification = Notification.Name("NagramiXTabInterfaceSoftRestartRequested")

    private enum Key {
        static let hideContacts = "nagramix.tabs.hideContacts"
        static let hideCalls = "nagramix.tabs.hideCalls"
        static let hideTitles = "nagramix.tabs.hideTitles"
        static let showSearchButton = "nagramix.tabs.showSearchButton"
        static let useRearCameraForVideoMessages = "nagramix.videoMessages.useRearCamera"
        static let hideStories = "nagramix.stories.hide"
        static let disableStoryCameraSwipe = "nagramix.stories.disableCameraSwipe"
        static let confirmStoryViewing = "nagramix.stories.confirmViewing"
        static let enableStoryRepost = "nagramix.stories.enableRepost"
    }

    public var hideContacts: Bool
    public var hideCalls: Bool
    public var hideTitles: Bool
    public var showSearchButton: Bool
    public var useRearCameraForVideoMessages: Bool
    public var hideStories: Bool
    public var disableStoryCameraSwipe: Bool
    public var confirmStoryViewing: Bool
    public var enableStoryRepost: Bool

    public init(
        hideContacts: Bool,
        hideCalls: Bool,
        hideTitles: Bool,
        showSearchButton: Bool,
        useRearCameraForVideoMessages: Bool,
        hideStories: Bool,
        disableStoryCameraSwipe: Bool,
        confirmStoryViewing: Bool,
        enableStoryRepost: Bool
    ) {
        self.hideContacts = hideContacts
        self.hideCalls = hideCalls
        self.hideTitles = hideTitles
        self.showSearchButton = showSearchButton
        self.useRearCameraForVideoMessages = useRearCameraForVideoMessages
        self.hideStories = hideStories
        self.disableStoryCameraSwipe = disableStoryCameraSwipe
        self.confirmStoryViewing = confirmStoryViewing
        self.enableStoryRepost = enableStoryRepost
    }

    public static var current: NagramiXTabSettings {
        let defaults = UserDefaults.standard
        return NagramiXTabSettings(
            hideContacts: defaults.object(forKey: Key.hideContacts) as? Bool ?? true,
            hideCalls: defaults.object(forKey: Key.hideCalls) as? Bool ?? true,
            hideTitles: defaults.object(forKey: Key.hideTitles) as? Bool ?? false,
            showSearchButton: defaults.object(forKey: Key.showSearchButton) as? Bool ?? false,
            useRearCameraForVideoMessages: defaults.object(forKey: Key.useRearCameraForVideoMessages) as? Bool ?? true,
            hideStories: defaults.object(forKey: Key.hideStories) as? Bool ?? false,
            disableStoryCameraSwipe: defaults.object(forKey: Key.disableStoryCameraSwipe) as? Bool ?? false,
            confirmStoryViewing: defaults.object(forKey: Key.confirmStoryViewing) as? Bool ?? false,
            enableStoryRepost: defaults.object(forKey: Key.enableStoryRepost) as? Bool ?? false
        )
    }

    public static func update(_ transform: (inout NagramiXTabSettings) -> Void) {
        var value = self.current
        transform(&value)

        let defaults = UserDefaults.standard
        defaults.set(value.hideContacts, forKey: Key.hideContacts)
        defaults.set(value.hideCalls, forKey: Key.hideCalls)
        defaults.set(value.hideTitles, forKey: Key.hideTitles)
        defaults.set(value.showSearchButton, forKey: Key.showSearchButton)
        defaults.set(value.useRearCameraForVideoMessages, forKey: Key.useRearCameraForVideoMessages)
        defaults.set(value.hideStories, forKey: Key.hideStories)
        defaults.set(value.disableStoryCameraSwipe, forKey: Key.disableStoryCameraSwipe)
        defaults.set(value.confirmStoryViewing, forKey: Key.confirmStoryViewing)
        defaults.set(value.enableStoryRepost, forKey: Key.enableStoryRepost)

        NotificationCenter.default.post(name: self.changedNotification, object: nil)
    }

    public static func requestTabInterfaceSoftRestart() {
        NotificationCenter.default.post(name: self.softRestartRequestedNotification, object: nil)
    }
}
