import Foundation

public struct NagramiXTabSettings: Equatable {
    public static let changedNotification = Notification.Name("NagramiXTabSettingsChanged")

    private enum Key {
        static let hideContacts = "nagramix.tabs.hideContacts"
        static let hideCalls = "nagramix.tabs.hideCalls"
        static let hideTitles = "nagramix.tabs.hideTitles"
        static let showSearchButton = "nagramix.tabs.showSearchButton"
    }

    public var hideContacts: Bool
    public var hideCalls: Bool
    public var hideTitles: Bool
    public var showSearchButton: Bool

    public init(
        hideContacts: Bool,
        hideCalls: Bool,
        hideTitles: Bool,
        showSearchButton: Bool
    ) {
        self.hideContacts = hideContacts
        self.hideCalls = hideCalls
        self.hideTitles = hideTitles
        self.showSearchButton = showSearchButton
    }

    public static var current: NagramiXTabSettings {
        let defaults = UserDefaults.standard
        return NagramiXTabSettings(
            hideContacts: defaults.object(forKey: Key.hideContacts) as? Bool ?? true,
            hideCalls: defaults.object(forKey: Key.hideCalls) as? Bool ?? true,
            hideTitles: defaults.object(forKey: Key.hideTitles) as? Bool ?? false,
            showSearchButton: defaults.object(forKey: Key.showSearchButton) as? Bool ?? false
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

        NotificationCenter.default.post(name: self.changedNotification, object: nil)
    }
}
