# NagramiX

NagramiX — независимый неофициальный Telegram-клиент для iOS. Кодовая база —
[Telegram-iOS](https://github.com/TelegramMessenger/Telegram-iOS), а выбранные
возможности [NagramX](https://github.com/risin42/NagramX) переносятся как
нативные функции iOS.

Проект оформлен как изолированный overlay, чтобы обновления Telegram-iOS было
проще переносить. GitHub Actions загружает зафиксированную ревизию upstream,
применяет слой NagramiX, собирает приложение arm64 без сертификата Apple и
упаковывает его для последующей подписи на стороне пользователя.

## Текущая версия: 0.1.2

- База: Telegram-iOS 12.9.2 (ревизия закреплена в `nagramix/upstream.env`).
- Ориентир функций: NagramX tag `1258` / 12.9.2.
- Bundle ID: `com.gamesfanteam.nagramix`.
- Добавлена официальная иконка NagramiX.
- Добавлено автоматическое переключение на доступный сохранённый прокси при
  длительной потере соединения; функция по умолчанию выключена.
- Результат сборки: неподписанный `NagramiX-0.1.2-unsigned.ipa`.
- Сертификаты Apple и данные подписи в репозитории не хранятся.

Для сборки нужны секреты репозитория `TELEGRAM_API_ID` и `TELEGRAM_API_HASH`,
полученные для приложения на <https://my.telegram.org/apps>. Это реквизиты
Telegram API, а не данные подписи Apple.

План, риски и чек-лист проверки через SideStore находятся в
[docs/BOOTSTRAP.md](docs/BOOTSTRAP.md).
