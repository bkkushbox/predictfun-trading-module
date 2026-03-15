# PredictFun Trading Module

[English](#english) | [Русский](#русский)

---

## English

Semi-automatic PredictFun trading module with confirmation-gated execution, hourly monitoring, 10-minute trigger checks, sell tracking, and fixed operational notifications.

### What this repository contains

This repository is a public-ready version of a real PredictFun operational workflow.

It is built for a user who wants useful automation, but does not want to give the bot uncontrolled trading power.

The module can:
- place buy orders for prepared markets;
- monitor private open orders;
- send hourly full reports;
- run 10-minute trigger checks for urgent changes;
- suggest replacements when prices move;
- ask for confirmation before replacement;
- switch into `SELL_HOLD_MODE` after a filled buy;
- track active sell orders;
- notify when a sale is completed;
- restart the cycle after user confirmation.

### Default markets included

The repository already includes a prepared default market set:
- OpenSea
- Base
- MetaMask

The user can start with this prepared set and add custom markets later.

See: `docs/PREDICTFUN_TARGET_MARKETS.json`

### Required setup

The user must add three values to a local env file:

```env
PREDICTFUN_API_KEY=
PREDICTFUN_WALLET_ADDRESS=
PREDICTFUN_PRIVATE_KEY=
```

What they mean:
- `PREDICTFUN_API_KEY` – PredictFun API key for API access
- `PREDICTFUN_WALLET_ADDRESS` – wallet or account address used by the module
- `PREDICTFUN_PRIVATE_KEY` – private key used to sign actions

Backward-compatible technical aliases are also supported:
- `PREDICTFUN_ACCOUNT_ADDRESS`
- `PREDICTFUN_PRIVY_PRIVATE_KEY`

### Security note

Never post these values in chat, never commit them to GitHub, and never store them in public files.

They must only exist locally on the user’s own machine.

### First run logic

After installation, the expected user flow is the following.

1. The module uses the prepared default markets.
2. The system asks the user to specify a budget.
3. It places buy orders according to the chosen logic.
4. It moves into monitoring mode.
5. If needed, it proposes replacements and asks for confirmation.
6. After a filled buy, it switches into sell monitoring.
7. After a filled sale, it asks whether to place orders again.

### Workflow examples

#### Step 1. Place orders

Example command:

```text
Place orders for market: MetaMask
Dates:
• June 30, 2026
• September 30, 2026
For each date:
• Yes $1
• No $1
```

Example notification:

```text
MetaMask – June 30, 2026
• market: Yes 12.3¢, No 87.8¢, spread 0.1¢
• your orders: Yes 9.3¢, No 84.8¢
❗️What to do:
Yes – ✅ placed
No – ✅ placed
```

#### Step 2. Monitoring and replace confirmation

```text
MetaMask – June 30, 2026
• market: Yes 13.8¢, No 86.3¢, spread 0.2¢
• your orders: Yes 9.3¢, No 84.8¢
❗️What to do:
Yes – ♻️ move to 10.8¢
No – ✅ no changes

Confirm replacement?
```

#### Step 3. Buy filled

```text
MetaMask – June 30, 2026
• market: Yes 13.8¢, No 86.3¢, spread 0.2¢
• your orders: Yes – filled, No 84.8¢
❗️What to do:
Yes – ✅ buy filled
No – ⏸️ pause

Switching to SELL_HOLD_MODE
```

#### Step 4. Sell watch

```text
MetaMask – June 30, 2026
• market: Yes 22.4¢, No 77.7¢, spread 0.1¢
• your orders: Sell Yes 29.0¢
❗️What to do:
Sell – 👀 watching
No – ⏸️ pause
```

#### Step 5. Sale completed

```text
MetaMask – June 30, 2026
• market: Yes 29.1¢, No 70.9¢, spread 0.1¢
• your orders: Sell Yes – filled
❗️What to do:
Sell – ✅ sold
Send: place orders again
```

#### Step 6. Cancel all buy orders

```text
Done. All buy orders cancelled.

• cancelled: 5 orders
• status: ✅ success
```

### Screenshots and workflow examples

Screenshots can be added as a visual companion to the workflow above.

Recommended structure:
- command to place orders;
- result notification;
- monitoring and replace confirmation;
- buy filled and `SELL_HOLD_MODE`;
- sell watch;
- sale completed.

Recommended rule:
- one screenshot per workflow step;
- short caption under each image;
- no secrets, wallet-sensitive data, API keys, chat ids, or private infrastructure details.

### Read these files next

- `QUICKSTART.md`
- `SECURITY.md`
- `docs/PREDICTFUN_OPERATIONS.md`
- `docs/PREDICTFUN_ARCHITECTURE.md`
- `docs/PREDICTFUN_TARGET_MARKETS.json`
- `examples/predictfun.env.example`

### Technical note

The correct cancel path for Predict accounts is:

- `POST /v1/orders/remove`

Do not assume SDK `cancelOrders()` matches real production behavior.

---

## Русский

Полуавтоматический модуль PredictFun с подтверждаемым исполнением, почасовым мониторингом, 10-минутными trigger-проверками, наблюдением за продажей и фиксированным форматом рабочих уведомлений.

### Что находится в репозитории

Это публично подготовленная версия реального рабочего сценария PredictFun.

Модуль сделан для пользователя, которому нужна полезная автоматизация, но без передачи боту полной свободы в торговых действиях.

Модуль умеет:
- выставлять buy-ордера по подготовленным рынкам;
- следить за приватными открытыми ордерами;
- присылать почасовые полные отчёты;
- каждые 10 минут проверять срочные сигналы;
- предлагать перестановку при движении рынка;
- спрашивать подтверждение перед replace;
- после исполнения buy-ордера переходить в `SELL_HOLD_MODE`;
- отслеживать активный sell-ордер;
- сообщать об исполнении продажи;
- после продажи запускать новый цикл по команде пользователя.

### Базовые рынки в комплекте

В репозитории уже есть подготовленный набор рынков:
- OpenSea
- Base
- MetaMask

Пользователь может сначала работать с этим набором, а позже добавить свои рынки.

См. `docs/PREDICTFUN_TARGET_MARKETS.json`

### Что нужно добавить в env

Пользователь должен добавить в локальный env-файл три значения:

```env
PREDICTFUN_API_KEY=
PREDICTFUN_WALLET_ADDRESS=
PREDICTFUN_PRIVATE_KEY=
```

Что значит каждая переменная:
- `PREDICTFUN_API_KEY` – API key от PredictFun для доступа к API
- `PREDICTFUN_WALLET_ADDRESS` – адрес кошелька или аккаунта, с которым работает модуль
- `PREDICTFUN_PRIVATE_KEY` – приватный ключ для подписи действий

Для совместимости также поддерживаются технические имена:
- `PREDICTFUN_ACCOUNT_ADDRESS`
- `PREDICTFUN_PRIVY_PRIVATE_KEY`

### Важное правило безопасности

Эти значения нельзя отправлять в чат, коммитить в GitHub или хранить в публичных файлах.

Они должны находиться только локально на машине пользователя.

### Логика первого запуска

После установки пользовательский сценарий должен быть таким.

1. Модуль использует подготовленные рынки.
2. Система запрашивает у пользователя бюджет.
3. Выставляет buy-ордера по выбранной логике.
4. Переходит в режим мониторинга.
5. При необходимости предлагает replace и ждёт подтверждения.
6. После исполнения покупки начинает следить за продажей.
7. После исполнения продажи просит новое действие.

### Примеры рабочего flow

#### Шаг 1. Выставление ордеров

Пример команды:

```text
Выстави ордера на Рынок: MetaMask.
Даты:
• June 30, 2026
• September 30, 2026
На каждую дату:
• Yes 1$
• No 1$
```

Пример уведомления:

```text
MetaMask – June 30, 2026
• рынок: Yes 12.3¢, No 87.8¢, spread 0.1¢
• твои ордера: Yes 9.3¢, No 84.8¢
❗️Что сделать:
Yes – ✅ выставлено
No – ✅ выставлено
```

#### Шаг 2. Мониторинг и подтверждение перестановки

```text
MetaMask – June 30, 2026
• рынок: Yes 13.8¢, No 86.3¢, spread 0.2¢
• твои ордера: Yes 9.3¢, No 84.8¢
❗️Что сделать:
Yes – ♻️ переставить на 10.8¢
No – ✅ без изменений

Подтверждаешь переставление?
```

#### Шаг 3. Покупка исполнена

```text
MetaMask – June 30, 2026
• рынок: Yes 13.8¢, No 86.3¢, spread 0.2¢
• твои ордера: Yes – исполнен, No 84.8¢
❗️Что сделать:
Yes – ✅ налили
No – ⏸️ пауза

Переходим в SELL_HOLD_MODE
```

#### Шаг 4. Наблюдение за продажей

```text
MetaMask – June 30, 2026
• рынок: Yes 22.4¢, No 77.7¢, spread 0.1¢
• твои ордера: Sell Yes 29.0¢
❗️Что сделать:
Sell – 👀 наблюдаю
No – ⏸️ пауза
```

#### Шаг 5. Продажа исполнена

```text
MetaMask – June 30, 2026
• рынок: Yes 29.1¢, No 70.9¢, spread 0.1¢
• твои ордера: Sell Yes – исполнен
❗️Что сделать:
Sell – ✅ продалось
Напиши: выстави заново ордера
```

#### Шаг 6. Отмена всех buy-ордеров

```text
Готово. Все buy-ордера отменены.

• отменено: 5 ордеров
• статус: ✅ success
```

### Скриншоты и примеры workflow

Скриншоты можно добавить как визуальное сопровождение к шагам выше.

Рекомендуемая структура:
- команда на выставление ордеров;
- итоговое уведомление;
- мониторинг и подтверждение перестановки;
- исполнение покупки и `SELL_HOLD_MODE`;
- наблюдение за продажей;
- исполнение продажи.

Рекомендуемое правило:
- один скриншот на один шаг workflow;
- короткая подпись под каждой картинкой;
- без секретов, чувствительных wallet-данных, API keys, chat ids и private infrastructure details.

### Что читать дальше

- `QUICKSTART.md`
- `SECURITY.md`
- `docs/PREDICTFUN_OPERATIONS.md`
- `docs/PREDICTFUN_ARCHITECTURE.md`
- `docs/PREDICTFUN_TARGET_MARKETS.json`
- `examples/predictfun.env.example`

### Техническое замечание

Для Predict account корректный путь отмены ордеров:

- `POST /v1/orders/remove`

Не стоит полагаться на то, что SDK `cancelOrders()` повторяет реальное прод-поведение один в один.
