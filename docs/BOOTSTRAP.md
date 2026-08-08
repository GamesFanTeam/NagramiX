# Bootstrap plan and risk map

## Scope and upstream observations

Telegram-iOS is a Bazel-based Swift/Objective-C application. Its supported device
build entry point is `build-system/Make/Make.py`, with `release_arm64` producing
the iPhone build. The current `versions.json` reports application 12.9.2, Xcode
26.2, Bazel 8.4.2 and macOS 26.

NagramX tag `1258` also identifies application version 12.9.2. It is an Android
codebase and is used only as a behavior/design reference. No Android source is
compiled or linked into NagramiX.

## Bootstrap phases

1. Keep the NagramiX-owned layer in `nagramix/`, `scripts/`, and `.github/`.
2. Resolve pinned Telegram-iOS commit `6ad963e5b62d354da79040f388ae2b9132fb17b8`
   in CI and verify version 12.9.2.
3. Generate build configuration from repository secrets; never commit API hashes,
   profiles, certificates, private keys, or Apple account data.
4. Apply deterministic branding and bundle configuration.
5. Build `release_arm64` with Telegram's fake-code-signing fixtures.
6. remove residual signatures/profiles and package `Payload/NagramiX.app` as
   `NagramiX.ipa`.
7. Sign/install with SideStore and validate launch plus Telegram authorization.
8. Only after the checkpoint passes, inventory NagramX 1258 features and port
   them in isolated iOS modules by coherent feature groups.

## Risk map

| Risk | Impact | Mitigation / gate |
|---|---|---|
| GitHub runner image differs from required Xcode 26.2/macOS 26 | Build cannot start | Use `macos-26`, verify the first run, and adjust only to an available image compatible with `versions.json`. |
| Updating the pinned upstream commit changes build inputs | Regressions or overlay failure | Update the SHA explicitly, review upstream changes, and let exact overlay checks fail loudly. |
| Fake signing still leaves entitlements or nested signatures | SideStore rejects or app crashes | Strip `_CodeSignature` and provisioning profiles; inspect every nested bundle before checkpoint approval. |
| App extensions require unavailable entitlements | Installation or launch fails | First green iteration may disable nonessential extensions; add them back individually after authorization works. |
| Separate URL schemes/keychain groups are incomplete | Login callback or stored session fails | Use a distinct scheme and bundle prefix; test cold launch, login, restart, and session persistence on-device. |
| Telegram API credentials are missing/incorrect | Authorization fails | Fail CI early; use credentials registered for NagramiX at `my.telegram.org`. |
| Branding touches broad upstream code | Upstream merges become expensive | Keep exact transformations in one overlay script and fail loudly when upstream layout changes. |
| GitHub artifact is called “unsigned” but contains a stale signature | SideStore re-signing behaves inconsistently | Strip signatures explicitly and add a package inspection step after first build. |
| GitHub Actions storage/runtime cost | Slow or unavailable builds | Cache Bazel artifacts, retain IPA for 14 days, and use manual builds outside bootstrap PRs. |
| Telegram/NagramX licensing and trademark obligations | Distribution risk | Remain clearly unofficial, use a distinct name/icon, publish modified source and preserve upstream notices. |

## Checkpoint acceptance

- GitHub Actions completes on a macOS runner without Apple signing secrets.
- Artifact contains one arm64 iPhone application under `Payload/NagramiX.app`.
- SideStore signs and installs it under `com.gamesfanteam.nagramix`.
- The app launches as NagramiX, completes Telegram authorization, survives a
  relaunch, and retains the session.
- Build provenance identifies the exact Telegram-iOS commit.

The bootstrap is not complete until all five checks have been confirmed on the
user's iPhone.
