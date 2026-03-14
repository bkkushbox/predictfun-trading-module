#!/usr/bin/env bash
set -euo pipefail
OC_BIN="/home/alex/.local/npm-global/bin/openclaw"
WORKDIR="/home/alex/.openclaw/workspace"
TARGET="8628999960"
MSG=$(python3 "$WORKDIR/scripts/predictfun_private_summary.py")
if [ -z "$MSG" ]; then
  exit 0
fi
"$OC_BIN" message send --channel telegram --target "$TARGET" --message "$MSG" >/dev/null
