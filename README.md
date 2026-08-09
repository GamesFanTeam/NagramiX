# NagramiX

**NagramiX** — независимый неофициальный клиент Telegram для iOS.

Проект использует [Telegram-iOS](https://github.com/TelegramMessenger/Telegram-iOS) в качестве исходной кодовой базы и переносит отдельные идеи и возможности из [NagramX](https://github.com/risin42/NagramX), реализуя их как нативные функции для iOS.

Репозиторий намеренно построен по принципу **overlay**, а не как полноценный форк Telegram-iOS с сотнями тысяч upstream-файлов.

Во время сборки CI:

1. загружает зафиксированную ревизию Telegram-iOS;
2. применяет поверх неё небольшой слой изменений NagramiX;
3. собирает приложение для реального iOS-устройства с архитектурой `arm64` без Apple-сертификата;
4. упаковывает результат в `NagramiX.ipa` для последующей подписи и установки через SideStore.

## Текущее состояние bootstrap

* Базовая версия приложения: **Telegram-iOS 12.9.2**
* Ветка upstream: `master`
* Зафиксированная ревизия хранится в `nagramix/upstream.env`
* Android-референс возможностей: **NagramX tag `1258` / 12.9.2**
* Bundle ID при нативной сборке: `com.gamesfanteam.nagramix`
* Apple-сертификаты и другие signing-данные в репозитории **не хранятся**
* Результат сборки: неподписанный `NagramiX.ipa` в артефактах GitHub Actions

## Telegram API

Перед первым запуском workflow необходимо добавить в **GitHub Actions Secrets** репозитория:

* `TELEGRAM_API_ID`
* `TELEGRAM_API_HASH`

Получить их необходимо для приложения NagramiX на:

https://my.telegram.org/apps

Это учётные данные **Telegram API**, а не сертификаты или данные для подписи Apple.

## Сборка и установка

GitHub Actions автоматически подготавливает неподписанный файл:

`NagramiX.ipa`

После завершения сборки IPA можно скачать из артефактов workflow, подписать и установить на устройство через **SideStore**.

## Документация

Подробный план реализации, известные риски bootstrap-процесса и чек-лист тестирования через SideStore находятся в:

[`docs/BOOTSTRAP.md`](docs/BOOTSTRAP.md)

---

> NagramiX является независимым неофициальным проектом и не связан с Telegram Messenger Inc.
