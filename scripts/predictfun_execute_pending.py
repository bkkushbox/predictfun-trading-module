#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from predictfun_paths import ENV_PATH, REPLACE_PLAN_PATH

PLAN_PATH = REPLACE_PLAN_PATH
HELPER = str(Path(__file__).resolve().parent / 'predictfun_execute_plan.mjs')


def main():
    if not PLAN_PATH.exists():
        print('NO_PLAN')
        return
    payload=json.loads(PLAN_PATH.read_text())
    generated_at = payload.get('generatedAt')
    if generated_at:
        try:
            dt = datetime.fromisoformat(generated_at)
            age = (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds()
            if age > 900:
                print('STALE_PLAN')
                return
        except Exception:
            pass
    plan=payload.get('plan',[])
    if not plan:
        print('NO_PLAN')
        return
    proc = subprocess.run(['node', HELPER, ENV_PATH, str(PLAN_PATH)], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or 'predictfun execute failed')
    PLAN_PATH.unlink(missing_ok=True)
    print(proc.stdout.strip())

if __name__ == '__main__':
    main()
