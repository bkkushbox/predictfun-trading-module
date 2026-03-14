#!/usr/bin/env bash
set -euo pipefail
OC_BIN="/home/alex/.local/npm-global/bin/openclaw"
WORKDIR="/home/alex/.openclaw/workspace"
TARGET="8628999960"
OUT_TXT="/tmp/predictfun_replace_plan.txt"

python3 "$WORKDIR/scripts/predictfun_replace_plan.py" > "$OUT_TXT"
if grep -qx 'NO_CHANGES' "$OUT_TXT"; then
  exit 0
fi
MSG=$(cat "$OUT_TXT")
"$OC_BIN" message send --channel telegram --target "$TARGET" --message "$MSG" >/dev/null
