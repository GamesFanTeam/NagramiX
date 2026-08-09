# Аудит NagramiX 0.1.2: расширенные настройки и автопереключение прокси

Дата аудита: 9 августа 2026 года.

## Зафиксированная база

- NagramiX: рабочая версия `v0.1.1`, commit `e75f0cdd825b82d88cba6611c75fe89c30f80f0c`.
- Telegram-iOS: commit `6ad963e5b62d354da79040f388ae2b9132fb17b8`, версия 12.9.2.
- Android-референс NagramX: tag `1258`, commit `ee899eff5a4980ae4f9eca7f60227029b95cbe07`.
- Новые функции должны оставаться overlay-слоем NagramiX и не должны мешать обновлению Telegram-iOS.
- Все параметры, меняющие стандартное поведение Telegram, по умолчанию выключены.

## Краткий вывод

Текущая архитектура Telegram-iOS позволяет корректно добавить отдельный экран «Настройки NagramiX» и настоящий proxy failover без второго сетевого стека. В проекте уже есть типизированные `ProxySettings`, список SOCKS5/MTProto-прокси, активный сервер, реактивное хранилище `AccountManager`, проверка доступности через `MTProxyConnectivity` и автоматическое применение нового сервера ко всем соединениям аккаунта.

Android NagramX 1258 действительно содержит `ProxyRotationController`. Он использует интервалы 5/10/15/30/60 секунд, по умолчанию выключен, запускает проверку при длительном состоянии подключения через прокси и выбирает доступный сервер. Это полезный функциональный референс, но Android-код напрямую переносить на iOS нельзя.

Полный перечень настроек из ТЗ затрагивает десятки независимых подсистем. Реализовывать их одним хаотичным патчем небезопасно. Версия 0.1.2 должна сначала заложить типизированный слой настроек, отдельный экран, иконку и proxy failover; остальные подтверждённые функции следует подключать группами с отдельной проверкой поведения.

## 1. Где реализован главный экран Settings

Главный экран настроек — это профильный экран аккаунта в режиме `isSettings`:

- `submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreen.swift` — контроллер, навигация и жизненный цикл;
- `submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoSettingsItems.swift` — секции и строки главного экрана;
- `submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreenSettingsActions.swift` — переходы в дочерние настройки;
- `submodules/TelegramUI/Sources/TelegramRootController.swift` — создание settings-вкладки;
- `submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoData.swift` — реактивные данные экрана.

UI построен на существующих компонентах `PeerInfoScreenDisclosureItem`, `ItemListController`, `ItemListSwitchItem`, `ItemListDisclosureItem` и автоматически наследует тему, Dynamic Type и общую навигацию.

## 2. Где добавить «Настройки NagramiX»

Нужно добавить отдельный элемент в `PeerInfoSettingsItems.swift`, новое значение `PeerInfoSettingsSection` и переход в `PeerInfoScreenSettingsActions.swift`. Экран следует реализовать как штатный `ItemListController`, а не как отдельную дизайн-систему.

Рекомендуемое положение — самостоятельная секция сразу после основных Telegram-настроек и до блока поддержки. Точное пользовательское название:

- русский: «Настройки NagramiX»;
- английский: `NagramiX Settings`.

## 3. Как устроено хранение настроек

Telegram-iOS использует типизированные `Codable`-структуры и реактивное хранилище:

- общие настройки приложения хранятся в `AccountManager.sharedData`;
- ключи приложения объявляются в `ApplicationSpecificSharedDataKeys`;
- значения оборачиваются в `PreferencesEntry`/`SharedPreferencesEntry`;
- обновления выполняются транзакциями `accountManager.transaction`;
- UI подписывается на `sharedData(keys:)` через SwiftSignalKit;
- декодирование новых полей должно иметь безопасные значения по умолчанию для миграции со старой версии.

Для NagramiX нужен единый `NagramiXSettings: Codable, Equatable`, централизованные defaults и одна функция `updateNagramiXSettingsInteractively`. Рассыпать строковые ключи и отдельные `UserDefaults` по UI нельзя.

Proxy-настройки уже хранятся отдельно в `ProxySettings` (`SyncCore_ProxySettings.swift`) и содержат:

- `enabled`;
- `servers`;
- `activeServer`;
- `useForCalls`.

Параметры auto switch логично добавить в эту же миграционно-безопасную модель либо в отдельную вложенную типизированную структуру, но не дублировать список прокси.

## 4–8. Инвентаризация функций ТЗ

Статусы:

- **A** — уже реализовано и может быть переиспользовано;
- **B** — реализовано частично, нужна безопасная интеграция/настройка;
- **C** — отсутствует, но реализуемо средствами текущего проекта;
- **D** — требует низкоуровневых изменений нескольких подсистем;
- **E** — нельзя корректно реализовать на текущем API либо нельзя обещать точный результат.

| Блок | Статус | Результат аудита |
|---|---:|---|
| Компактный список и превью чатов | D | Chat List уже существует, но публичного параметра плотности нет. Нужны изменения layout существующих item nodes, без второго списка. |
| Свайп-опции чатов | B/C | Штатные свайп-действия существуют. Можно расширять их конфигурацию, сохраняя permission checks. |
| Свайп для удаления чата | C | Реализуем через существующий delete flow и подтверждения; нельзя обходить серверную семантику удаления. |
| Нижняя панель каналов, широкие посты | D | Затрагивает ChatController/Channel message layout и требует отдельного визуального тестирования. |
| Секунды во времени сообщений | C | Timestamp уже форматируется в Message UI; можно добавить параметр формата без параллельного UI. |
| Редактирование двойным тапом | C | Инфраструктура double-tap уже есть; действие надо подключать только для редактируемых собственных сообщений. |
| Кнопка голоса, камера и её превью в галерее | B/D | Компоненты уже существуют, но их видимость и camera pipeline распределены по Chat input/media picker. |
| Свайпы между каналами/топиками | D | Требуют изменений навигации и конфликтуют с системным back gesture; нужны отдельные gesture tests. |
| Скрыть реакции | C | Reaction UI существует; возможно локально скрыть отображение, не меняя данные Telegram. |
| Действия контекстного меню | A/B/C | Reply, pin, report, restrict, save/share и просмотр ответов уже формируются штатным menu builder с permission checks. Нужен фильтр NagramiX поверх доступных действий. JSON — отдельное безопасное техническое представление без секретов. |
| ID профиля/чата | A/C | `PeerId` доступен клиенту и может быть показан локально. |
| DC профиля | E/B | Универсального «DC пользователя» Telegram API не предоставляет. Можно показывать только DC конкретного доступного ресурса с точной подписью, не выдавая его за DC аккаунта. |
| Дата регистрации/создания чата | E | Точная дата API не предоставляется. Приближение по ID ненадёжно; без явно маркированной доказуемой оценки функцию не показывать. |
| Подтверждение исходящего вызова | C | Реализуемо перед штатным `requestCall`; входящие вызовы не затрагиваются. |
| Force TCP | B | В `ExperimentalUISettings` уже есть `enableVoipTcp`; требуется доказать, что активная версия VoIP его потребляет, и только затем вывести настройку. |
| Качество и большие фото | D | Есть штатный media pipeline и JPEG-компрессия, но параметр 0–100 нельзя подставлять без проверки всех путей отправки и серверных лимитов. |
| Размер стикеров/эмодзи | D | Layout существует в нескольких message/keyboard nodes. Нужен общий коэффициент на уровне layout, не transform hack. |
| Задняя камера для круглых видео | C | Camera session уже поддерживает переключение; можно изменить только начальный route и не сбрасывать ручной выбор. |
| Истории | B/C/D | Stories полностью реализованы. Скрытие UI и запрос подтверждения реализуемы; отключение/добавление жестов требует проверки конфликтов; репост уже частично поддерживается штатно. |
| Перевод | A/B | Telegram Translation и `TranslationSettings` существуют. Быстрая кнопка/целый чат частично существуют. Сторонние сервисы требуют отдельного API и политики секретов. |
| Голос в текст | A/B | Штатная Telegram transcription существует; `localTranscription` присутствует как experimental flag. Системный Speech framework требует отдельной реализации и разрешений. |
| Микрофон устройства | B/D | `ManagedAudioSession` уже работает с `availableInputs`, `builtInMic` и `setPreferredInput`. Глобальный пользовательский override требует аккуратной интеграции с calls/recording/interruption lifecycle. |
| Настройки emoji-клавиатуры | B/C | Клавиатура уже модульная; отправка Enter и начальная вкладка реализуемы как параметры существующего компонента. |
| Локально скрыть номер | C | Реализуемо как presentation-фильтр. Не должно менять Telegram Privacy Settings и не должно скрывать номер в функционально необходимых формах. |
| Видео PiP свайпом | A/C | В GalleryUI и UniversalVideo уже есть native/custom PiP. Нужен только opt-in жест, вызывающий существующий pipeline. |
| Персональные цвета/насыщенность | A/B/D | Telegram theme/name/profile color уже есть. Accent можно переиспользовать; произвольная насыщенность затрагивает theme generation и требует отдельного исследования. |
| SOCKS5 и MTProto proxy | A | Полностью поддерживаются моделью `ProxyServerConnection`. |
| Список, выбор и удаление proxy | A | Уже реализованы в `ProxyListSettingsController.swift`. |
| Статусы proxy | A/B | `ProxyServersStatuses` выдаёт checking/notAvailable/available(ping), но текущий экран создаёт проверки на время своей жизни. |
| Автопереключение proxy | C | На iOS отсутствует; реализуемо поверх текущих моделей и `MTProxyConnectivity`. |

## 9. Где реализован Proxy

- `submodules/TelegramCore/Sources/SyncCore/SyncCore_ProxySettings.swift` — модели SOCKS5/MTProto, список и активный сервер;
- `submodules/TelegramCore/Sources/Settings/ProxySettings.swift` — атомарное обновление shared data;
- `submodules/SettingsUI/Sources/Data and Storage/ProxyListSettingsController.swift` — существующий экран списка;
- `submodules/SettingsUI/Sources/Data and Storage/ProxyServerSettingsController.swift` — добавление и редактирование;
- `submodules/TelegramCore/Sources/Network/ProxyServersStatuses.swift` — ping/status через `MTProxyConnectivity`;
- `submodules/TelegramCore/Sources/Account/Account.swift` — применение активного proxy к живому `Network`;
- `submodules/TelegramCore/Sources/Network/Network.swift` — начальная настройка MTProto environment.

## 10. Как выбирается active proxy

При выборе строки существующий контроллер транзакционно устанавливает `current.activeServer = server` и `current.enabled = true`. При удалении активного сервера `activeServer` очищается и proxy выключается. Порядок серверов можно менять drag-and-drop; он сохраняется в `ProxySettings.servers`.

`ProxySettings.effectiveActiveServer` возвращает сервер только при `enabled == true`. `Account.swift` подписан на это значение. При изменении он вызывает `network.dropConnectionStatus()` и обновляет `MTApiEnvironment.socksProxySettings`, то есть отдельный reconnect-код для NagramiX не нужен.

## 11. Как выполняется proxy ping/check

`ProxyServersStatuses` создаёт `ProxyServerItemContext` для каждого сохранённого сервера. Проверка выполняется штатным `MTProxyConnectivity.pingProxy`, результат преобразуется в:

- `.checking`;
- `.notAvailable`;
- `.available(roundTripTime)`.

Текущий объект связан с жизнью proxy-экрана и не является вечным scheduler. Для auto switch нужно вынести переиспользуемую one-shot проверку в TelegramCore и управлять её отменой независимо от UI.

## 12. Есть ли существующий reconnect/failover

Автоматический reconnect при смене `effectiveActiveServer` уже есть: `Account.swift` обновляет network environment и сбрасывает connection status. Автоматического перебора следующего сохранённого proxy в iOS нет.

Следовательно, NagramiX должен выбирать следующий сервер и записывать его в существующий `ProxySettings`; сам reconnect продолжит выполнять TelegramCore.

## 13. Android NagramX 1258

Аналог найден:

- `TMessagesProj/src/main/java/org/telegram/messenger/ProxyRotationController.java`;
- `TMessagesProj/src/main/java/org/telegram/ui/ProxyListActivity.java`;
- `TMessagesProj/src/main/java/org/telegram/messenger/SharedConfig.java`.

Поведение Android:

- feature по умолчанию выключена;
- доступна при включённом proxy и минимум двух серверах;
- интервалы: 5, 10, 15, 30, 60 секунд;
- scheduler реагирует на `ConnectionStateConnectingToProxy`;
- проверяет серверы штатным `checkProxy`;
- выбирает доступный сервер, предпочтительно с меньшим ping;
- отменяет отложенную задачу при изменении proxy settings;
- сохраняет enabled/timeout в preferences.

Это ближе к **failover**, чем к постоянной rotation: исправный стабильный proxy без причины не меняется. Именно такая семантика соответствует пункту 24 ТЗ и безопаснее для iOS.

## 14. Предполагаемая карта изменений

Overlay NagramiX:

- новый типизированный settings-модуль и pure policy для auto switch;
- новый `ItemListController` «Настройки NagramiX»;
- ресурсы русской/английской локализации;
- набор AppIcon из предоставленного исходника;
- unit tests policy/scheduler;
- расширение `apply_overlay.py` для детерминированного копирования файлов и минимальных pinned patches;
- workflow и упаковщик с именем `NagramiX-0.1.2-unsigned.ipa`.

Минимальные точки интеграции Telegram-iOS:

- `PeerInfoScreen.swift`;
- `PeerInfoSettingsItems.swift`;
- `PeerInfoScreenSettingsActions.swift`;
- соответствующие `BUILD`-файлы;
- `SyncCore_ProxySettings.swift` либо отдельный NagramiX proxy preference;
- `ProxySettings.swift`;
- `ProxyServersStatuses.swift`;
- `ProxyListSettingsController.swift`;
- lifecycle-владелец на уровне `Account`/`SharedAccountContext`;
- localization resources;
- AppIcon assets/BUILD configuration.

Точные файлы каждой дополнительной пользовательской функции следует фиксировать после отдельного узкого аудита её subsystem перед реализацией.

## 15. Предлагаемая архитектура

### Слой настроек

`NagramiXSettings` — одна `Codable, Equatable` структура с типизированными вложенными группами и миграционно-безопасным decoding. Все экспериментальные параметры default `false`; числовые параметры имеют централизованные bounds/defaults.

### Экран

`NagramiXSettingsController` использует существующий `ItemListController`, тему, шрифты, accessibility и локализацию Telegram. В UI добавляются только реально подключённые параметры. Заглушки и переключатели без поведения запрещены.

### Proxy Auto Switch

1. `ProxyAutoSwitchInterval` — enum: 5/10/15/30/60 секунд.
2. `ProxyAutoSwitchPolicy` — чистая логика выбора следующего кандидата и edge cases.
3. `ProxyHealthChecker` — отменяемая one-shot обёртка над `MTProxyConnectivity`.
4. `ProxyAutoSwitchCoordinator` — один queue-confined lifecycle-владелец на аккаунт/общий proxy state.
5. Coordinator подписывается на proxy settings, network status и foreground/reachability.
6. При стабильном соединении текущий proxy не меняется.
7. При timeout/неудаче кандидаты проверяются последовательно, начиная со следующего в сохранённом порядке.
8. Успешный кандидат записывается через `updateProxySettingsInteractively`; штатный `Account.swift` выполняет reconnect.
9. Generation token отбрасывает stale-result после удаления proxy, смены интервала или выключения feature.
10. `MetaDisposable`/queue lifecycle гарантируют один scheduler и одну активную проверку; busy loop запрещён.
11. При offline проверки приостанавливаются, после восстановления сети scheduler возобновляется.
12. При 0/1 proxy scheduler не запускается; при полном отказе всех серверов выполняется следующий обычный scheduled retry.

### Разделение режимов

Для 0.1.2 рекомендуется только режим **Failover**: здоровый proxy не меняется. Режим **Rotation** (принудительная периодическая смена даже исправного сервера) можно добавить позднее отдельным enum после проверки реальной потребности; смешивать две семантики в одном switch нельзя.

## Риски

| Риск | Уровень | Снижение риска |
|---|---:|---|
| Несколько scheduler/reconnect loops | высокий | один coordinator, queue confinement, generation token, MetaDisposable |
| Агрессивные проверки расходуют батарею | высокий | проверки только при включённой функции и проблемном соединении, остановка offline/background |
| Смена proxy во время удаления/редактирования | высокий | сверка с актуальным списком перед commit, stale-result rejection |
| Нарушение авторизации/базовой сети 0.1.1 | высокий | использовать только существующий `ProxySettings` и штатное применение в `Account.swift` |
| Большой upstream diff | высокий | isolated overlay, отдельные pinned patches, без fork-wide рефакторинга |
| Fake UI из большого перечня настроек | высокий | показывать только настройку с подключённым поведением и тестом |
| Android/iOS архитектурные различия | средний | переносить семантику, а не Java/Android lifecycle |
| Локализация сломается при генерации strings | средний | штатные resources, минимум ru/en, CI-проверка ключей |
| AppIcon содержит неподходящие alpha/размеры | средний | генерировать полный asset set и проверять PNG/Info.plist в IPA |

## План реализации после аудита

1. **Фундамент 0.1.2:** иконка, версия/имя unsigned IPA, typed settings module, локализация, пункт и пустой только навигационно завершённый экран (без неработающих switches).
2. **Proxy UI/state:** auto switch OFF по умолчанию, interval enum, отображение только при двух и более proxy.
3. **Proxy engine:** policy, health checker, coordinator, lifecycle, network recovery.
4. **Proxy tests:** defaults, persistence, intervals, 0/1/2/3+ серверов, failover, все недоступны, удаление, stale result, смена interval, ON/OFF, duplicate scheduler, offline/recovery.
5. **Первая группа NagramiX-функций:** только функции категории C с коротким безопасным путём — например, секунды времени, подтверждение вызова, локальное скрытие номера — каждая отдельным проверяемым блоком.
6. **CI:** ARM64 build, анализ IPA, имя `NagramiX-0.1.2-unsigned.ipa`, отсутствие подписи/profile, Bundle ID, AppIcon, SHA-256.
7. **Проверка на iPhone:** обновление поверх 0.1.1, сохранение авторизации, proxy edge cases и обычная работа без proxy.

## Решение по фазе AUDIT

Аудит подтверждает техническую реализуемость двух главных блоков ТЗ. Начинать реализацию можно без дополнительных продуктовых вопросов при следующих зафиксированных правилах:

- 0.1.1 остаётся стабильной базой;
- auto switch означает failover, а не бессмысленную смену здорового сервера;
- feature по умолчанию OFF;
- разрешены только 5/10/15/30/60 секунд;
- никаких fake switches;
- точные недоступные данные профиля не выдумываются;
- итоговый файл: `NagramiX-0.1.2-unsigned.ipa`;
- релиз и документация ведутся на русском языке.
