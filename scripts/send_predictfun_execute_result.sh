#!/usr/bin/env bash
set -euo pipefail
OC_BIN="/home/alex/.local/npm-global/bin/openclaw"
WORKDIR="/home/alex/.openclaw/workspace"
TARGET="8628999960"
OUT_JSON="/tmp/predictfun_execute_result.json"

python3 "$WORKDIR/scripts/predictfun_execute_pending.py" > "$OUT_JSON"
STATUS=$(python3 - <<'PY'
import json,sys
raw=open('/tmp/predictfun_execute_result.json').read().strip()
print(raw)
PY
)
if [ "$STATUS" = "NO_PLAN" ]; then
  "$OC_BIN" message send --channel telegram --target "$TARGET" --message "Нет активного плана на переставление." >/dev/null
  exit 0
fi
if [ "$STATUS" = "STALE_PLAN" ]; then
  "$OC_BIN" message send --channel telegram --target "$TARGET" --message "План переставления устарел. Нужен новый trigger/пересчёт." >/dev/null
  exit 0
fi
MSG=$(python3 - <<'PY'
import json
j=json.load(open('/tmp/predictfun_execute_result.json'))
rows=[]
for r in j.get('results',[]):
    if r.get('placed'):
        rows.append(f"**{r['project']} ({r['date']})**\n• рынок: ордер переставлен\n• твои ордера: {r['side']} {r['newPrice']*100:.1f}¢ ({r['newShares']:.2f} shares)\n❗️**Что делать:**\n• **{r['side']}** — переставление выполнено после твоего подтверждения.")
print('\n\n'.join(rows) if rows else 'Переставление не выполнено: пустой результат.')
PY
)
"$OC_BIN" message send --channel telegram --target "$TARGET" --message "$MSG" >/dev/null
