# NagramiX

**NagramiX** — независимый неофициальный клиент Telegram для iOS.

Проект использует [Telegram-iOS](https://github.com/TelegramMessenger/Telegram-iOS)
как кодовую базу и переносит отдельные возможности
[NagramX](https://github.com/risin42/NagramX) как нативные функции iOS.

## Текущая версия: 0.1.2

- База: Telegram-iOS 12.9.2, закреплённая в `nagramix/upstream.env`.
- Ориентир функций: NagramX tag `1258` / 12.9.2.
- Bundle ID: `com.gamesfanteam.nagramix`.
- Установлена официальная иконка NagramiX.
- Добавлено автоматическое переключение на доступный сохранённый прокси при
  длительной потере соединения; функция по умолчанию выключена.
- Результат сборки: `NagramiX-0.1.2-unsigned.ipa` без Apple-подписи.

GitHub Actions применяет изолированный overlay NagramiX к закреплённой ревизии
upstream и собирает arm64-приложение. Сертификаты Apple и данные подписи в
репозитории не хранятся. Для сборки используются секреты `TELEGRAM_API_ID` и
`TELEGRAM_API_HASH`, полученные на <https://my.telegram.org/apps>.

План, риски и чек-лист проверки через SideStore находятся в
[docs/BOOTSTRAP.md](docs/BOOTSTRAP.md).

---

> NagramiX является независимым неофициальным проектом и не связан с Telegram Messenger Inc.
