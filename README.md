# PredictFun Trading Module

[English](#english) | [Русский](#русский)

---

## English

A semi-automatic trading module for PredictFun with private order monitoring, `SELL_HOLD_MODE`, confirmation-gated execution, and fixed operational notifications.

### What this repository is

This repository is a public-ready version of a real operational PredictFun trading workflow. It is built for a user who wants automation where it is useful, but does not want to give the bot full freedom over trading actions.

The module can:
- monitor private open orders;
- detect fills and switch into `SELL_HOLD_MODE`;
- stay quiet after the pause notification instead of spamming;
- track the active sell order;
- prepare fresh `Yes + No` buy orders;
- suggest replacements when the market moves;
- execute placement or replacement only after explicit confirmation.

### Core principles

- Monitoring can run automatically.
- Trading actions stay confirmation-gated.
- Buy placement, replace flow, and cleanup require explicit approval.
- After a fill, the module pauses correctly and avoids noisy alerts.
- The live sell order is preserved during buy-side cleanup.

### Confirmed in live tests

The following behaviors were confirmed in production-style tests:
- place one buy order;
- place `Yes + No` buy orders;
- replace `Yes + No` after explicit confirmation;
- cancel test buy orders;
- keep the active sell order untouched during cleanup;
- use the correct private cancel flow through `POST /v1/orders/remove`.

### Main runtime flow

#### 1. Normal buy mode

The module monitors market state and private open orders. If current orders still match the target rules, it returns `NO_CHANGES`. If a replacement is needed, it sends a proposal and waits for explicit confirmation before executing it.

#### 2. After a fill

The module enters `SELL_HOLD_MODE` and sends one pause notification. After that, it stays quiet instead of repeating hourly noise.

#### 3. Sell order active

When the user places a sell order, the module detects it and sends a sell notification in a fixed operational format. Then it continues to monitor silently.

#### 4. Sell order no longer active

When the sell order disappears from open orders, the module sends a short status message and waits for one of two commands:
- `выстави сам`
- `ордера выставил сам`

#### 5. Replace flow

If the user wants the module to manage the buy side, it can place fresh `Yes + No` buy orders. If the market moves, it builds a replace plan, sends a proposal, and executes the replace only after confirmation.

### Repository structure

```text
predictfun-trading-module/
  README.md
  QUICKSTART.md
  SECURITY.md
  PUBLISHING_NOTES.md
  docs/
  examples/
  scripts/
```

### Read these files first

- `QUICKSTART.md` – quick start guide
- `SECURITY.md` – what must remain private
- `docs/PREDICTFUN_OPERATIONS.md` – full runtime logic and output behavior
- `docs/PREDICTFUN_ARCHITECTURE.md` – architecture and module layers
- `examples/predictfun.env.example` – env template
- `examples/runtime-layout.md` – suggested local folder layout

### Important technical note

The correct cancel path for the Predict account is:

- `POST /v1/orders/remove`

Do not assume SDK `cancelOrders()` matches real production behavior.

### Status

This repository is a sanitized public package. Real credentials, live environment files, JWT tokens, cookies, and operational secrets are intentionally excluded.

---

## Русский

Полуавтоматический модуль для торговли на PredictFun с мониторингом приватных ордеров, режимом `SELL_HOLD_MODE`, подтверждаемым исполнением действий и фиксированным форматом рабочих уведомлений.

### Что это за репозиторий

Это публично подготовленная версия реального рабочего модуля для сценариев PredictFun. Логика сделана для пользователя, которому нужна полезная автоматизация, но без передачи боту полной свободы в торговых действиях.

Модуль умеет:
- следить за приватными открытыми ордерами;
- определять исполнение и переходить в `SELL_HOLD_MODE`;
- отправлять одно pause-уведомление и не спамить дальше;
- отслеживать активный sell-ордер;
- готовить новые buy-ордера `Yes + No`;
- предлагать перестановку ордеров при движении рынка;
- исполнять выставление или replace только после явного подтверждения пользователя.

### Основные принципы

- Мониторинг может работать автоматически.
- Торговые действия остаются только через подтверждение.
- Выставление buy-ордеров, replace и cleanup не выполняются без явного согласия.
- После залива модуль корректно уходит в паузу и не создаёт шум.
- Активный sell-ордер не затрагивается при очистке buy-части.

### Что уже подтверждено тестами

В рабочем контуре уже были подтверждены следующие сценарии:
- выставление одного buy-ордера;
- выставление пары `Yes + No`;
- replace пары `Yes + No` после явного подтверждения;
- отмена тестовых buy-ордеров;
- сохранение активного sell-ордера при очистке;
- использование корректного приватного пути отмены через `POST /v1/orders/remove`.

### Основной рабочий сценарий

#### 1. Обычный buy-режим

Модуль следит за рынком и приватными открытыми ордерами. Если ордера соответствуют целевым правилам, возвращается `NO_CHANGES`. Если нужна перестановка, модуль формирует предложение и ждёт подтверждения перед исполнением.

#### 2. После исполнения ордера

Модуль переходит в `SELL_HOLD_MODE` и отправляет одно pause-уведомление. После этого не повторяет лишние почасовые сообщения.

#### 3. Активен sell-ордер

Когда пользователь выставляет sell-ордер, модуль это обнаруживает, отправляет уведомление в фиксированном рабочем формате и дальше молча наблюдает.

#### 4. Sell-ордер больше не активен

Когда sell-ордер исчезает из списка открытых ордеров, модуль отправляет короткий статус и ждёт одну из двух команд:
- `выстави сам`
- `ордера выставил сам`

#### 5. Replace flow

Если пользователь хочет, чтобы модуль вёл buy-сторону, он может выставлять новые buy-ордера `Yes + No`. Если рынок сдвигается, модуль собирает replace-plan, показывает предложение и исполняет его только после подтверждения.

### Структура репозитория

```text
predictfun-trading-module/
  README.md
  QUICKSTART.md
  SECURITY.md
  PUBLISHING_NOTES.md
  docs/
  examples/
  scripts/
```

### Что читать в первую очередь

- `QUICKSTART.md` – быстрый старт
- `SECURITY.md` – что обязательно должно оставаться приватным
- `docs/PREDICTFUN_OPERATIONS.md` – полная рабочая логика и формат вывода
- `docs/PREDICTFUN_ARCHITECTURE.md` – архитектура и слои модуля
- `examples/predictfun.env.example` – пример env-файла
- `examples/runtime-layout.md` – рекомендуемая локальная структура

### Важное техническое замечание

Для Predict account корректный путь отмены ордеров следующий:

- `POST /v1/orders/remove`

Не стоит полагаться на то, что SDK `cancelOrders()` повторяет реальное прод-поведение один в один.

### Статус

Репозиторий подготовлен как публичный и очищенный пакет. Реальные credentials, рабочие env-файлы, JWT, cookies и иные операционные секреты намеренно не включены.
