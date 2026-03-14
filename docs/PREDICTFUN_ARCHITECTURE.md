# PredictFun — итоговая модель модуля

## Общая модульная схема

### Модуль 1: News Monitor
Назначение:
- мониторинг новостей и внешних сигналов по интересующим проектам/токенам
- расширяемый список проектов
- ранние сигналы через X и news-источники

Текущий статус:
- уже настроен и работает
- логически считается отдельным модулем `News Monitor`

### Модуль 2: PredictFun
Назначение:
- серьёзный рабочий контур по рынкам PredictFun
- public market watcher
- private read-only layer
- в перспективе order management / semi-auto / trading layer

## Внутренняя архитектура модуля PredictFun

### Слой A — Public market watcher
Цель:
- следить за выбранными рынками и рыночной динамикой
- не требует private account access

Правильная логика target discovery:
1. сначала category truth:
   - `GET /v1/categories/{slug}`
2. затем берём `markets[]` из category response
3. фиксируем нужные market ids в target config
4. далее watcher уже работает по direct ids через `GET /v1/markets/{id}`

Текущие category slugs:
- `will-metamask-launch-a-token-in-2025`
- `will-base-launch-a-token-in-2026`
- `will-opensea-launch-a-token-by-142`

Роль:
- датчик изменения рыночных ожиданий
- не предсказывает истину, а показывает движение рынка

### Слой B — Private auth layer
Цель:
- обеспечить доступ к private endpoints

База:
- API key
- Export Privy Wallet
- predictAccount
- auth message
- signature
- JWT

### Слой C — Private read-only layer
Цель:
- видеть свой контекст в PredictFun

Что включает:
- orders
- positions
- balance
- account state

### Слой D — Trading / order management layer
Цель:
- actions с ордерами

Что включает:
- create order
- cancel orders
- replace logic
- redeem / merge

Уточнение по cancel flow:
- рабочий cancel-механизм для Predict account идёт через private API endpoint `POST /v1/orders/remove` c JWT + API key.
- SDK `cancelOrders()` не является единственным рабочим путём и может не совпадать с UI flow.

Важно:
- этот слой не должен включаться автоматически без зрелой модели и отдельного подтверждения
