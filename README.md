# NagramiX

NagramiX is an independent, unofficial Telegram client for iOS. The project uses
[Telegram-iOS](https://github.com/TelegramMessenger/Telegram-iOS) as its source
base and ports selected ideas from
[NagramX](https://github.com/risin42/NagramX) as native iOS features.

The bootstrap is intentionally an overlay instead of a fork containing hundreds
of thousands of upstream files. CI checks out a pinned Telegram-iOS revision,
applies the small NagramiX layer, builds an arm64 device application without an
Apple certificate, and packages `NagramiX.ipa` for later signing by SideStore.

## Bootstrap status

- Upstream application version: Telegram-iOS 12.9.2 (`master`, pinned in
  `nagramix/upstream.env`)
- Android feature reference: NagramX tag `1258` / 12.9.2
- Native build-time Bundle ID: `com.gamesfanteam.nagramix`
- Signing assets: none stored in this repository
- Output: unsigned `NagramiX.ipa` GitHub Actions artifact

The first workflow run requires repository secrets `TELEGRAM_API_ID` and
`TELEGRAM_API_HASH`, obtained for this app at <https://my.telegram.org/apps>.
These are Telegram API credentials, not Apple signing credentials.

See [docs/BOOTSTRAP.md](docs/BOOTSTRAP.md) for the implementation plan, risks,
and SideStore test checklist.
