import Foundation
import SwiftSignalKit
import TelegramCore
import NagramiXCore

final class NagramiXConfirmingStoryContentContext: StoryContentContext {
    private let source: StoryContentContext
    private let accountPeerId: EnginePeer.Id
    private let statePromise = Promise<StoryContentContextState>()
    private var decisionDisposable: Disposable?
    private(set) var isActivated: Bool = false
    private var confirmationIsRequired: Bool = false

    var requestConfirmation: (() -> Void)? {
        didSet {
            if self.confirmationIsRequired && !self.isActivated {
                self.requestConfirmation?()
            }
        }
    }

    init(source: StoryContentContext, accountPeerId: EnginePeer.Id) {
        self.source = source
        self.accountPeerId = accountPeerId
        self.statePromise.set(.single(StoryContentContextState(slice: nil, previousSlice: nil, nextSlice: nil)))

        self.decisionDisposable = (source.state
        |> filter { $0.slice != nil }
        |> take(1)
        |> deliverOnMainQueue).startStrict(next: { [weak self] state in
            guard let self else {
                return
            }
            if state.slice?.peer.id == self.accountPeerId {
                self.activate()
            } else {
                self.confirmationIsRequired = true
                self.requestConfirmation?()
            }
        })
    }

    deinit {
        self.decisionDisposable?.dispose()
    }

    var stateValue: StoryContentContextState? {
        if self.isActivated {
            return self.source.stateValue
        } else {
            return StoryContentContextState(slice: nil, previousSlice: nil, nextSlice: nil)
        }
    }

    var state: Signal<StoryContentContextState, NoError> {
        return self.statePromise.get()
    }

    var updated: Signal<Void, NoError> {
        return self.source.updated
        |> filter { [weak self] _ in
            return self?.isActivated == true
        }
    }

    func activate() {
        guard !self.isActivated else {
            return
        }
        self.isActivated = true
        self.confirmationIsRequired = false
        self.decisionDisposable?.dispose()
        self.decisionDisposable = nil
        self.statePromise.set(self.source.state)
    }

    func resetSideStates() {
        if self.isActivated {
            self.source.resetSideStates()
        }
    }

    func navigate(navigation: StoryContentContextNavigation) {
        if self.isActivated {
            self.source.navigate(navigation: navigation)
        }
    }

    func markAsSeen(id: EngineStoryId) {
        if self.isActivated {
            self.source.markAsSeen(id: id)
        }
    }
}
