#!/usr/bin/env bash
set -euo pipefail
OC_BIN="/home/alex/.local/npm-global/bin/openclaw"
WORKDIR="/home/alex/.openclaw/workspace"
OUT_JSON="/tmp/predictfun_public_alerts.json"
TARGET="8628999960"

python3 "$WORKDIR/scripts/predictfun_public_watcher.py" > "$OUT_JSON"
CNT=$(python3 - <<'PY'
import json
with open('/tmp/predictfun_public_alerts.json') as f:
    j=json.load(f)
print(len(j.get('alerts',[])))
PY
)
if [ "$CNT" = "0" ]; then
  exit 0
fi
PROMPT=$(cat <<'EOF'
Преобразуй сигналы public market watcher в понятные уведомления на русском.
Формат для каждого сигнала:

**PredictFun Alert — [Проект]**
**Что сработало:**
рынок / движение рынка

**Что нашли:**
коротко, что именно изменилось.

**Что это значит:**
простыми словами объясни, что рынок начал закладывать изменение ожиданий. Не выдавай это за доказательство того, что токен точно выйдет.

**Насколько это важно:**
только один из уровней: очень сильный / высокий / средний

**Что делать:**
что разумно сделать сейчас: проверить рынок / посмотреть даты / пересмотреть ставки.

Если сигналов несколько, разделяй пустой строкой. Без ссылок. Компактно. Без воды.
Перед отправкой:
1. проверь логичность
2. убедись что нет противоречий
3. убери лишние детали
4. улучши структуру

ДАННЫЕ СИГНАЛОВ:
EOF
)
DATA=$(cat "$OUT_JSON")
FULL_MSG="$PROMPT
$DATA"
"$OC_BIN" agent --agent main --message "$FULL_MSG" --deliver --reply-channel telegram --reply-to "$TARGET" --timeout 600 >/dev/null
