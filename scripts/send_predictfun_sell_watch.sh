#!/usr/bin/env bash
set -euo pipefail
OC_BIN="/home/alex/.local/npm-global/bin/openclaw"
WORKDIR="/home/alex/.openclaw/workspace"
TARGET="8628999960"
OUT="$($WORKDIR/scripts/predictfun_sell_watch.py)"
if [[ -z "$OUT" || "$OUT" == "NO_EVENT" ]]; then
  exit 0
fi
"$OC_BIN" message send --channel telegram --target "$TARGET" --message "$OUT" >/dev/null
