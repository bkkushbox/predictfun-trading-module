#!/usr/bin/env python3
from pathlib import Path
import os

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get('PREDICTFUN_DATA_DIR', REPO_ROOT / 'data'))
ENV_PATH = Path(os.environ.get('PREDICTFUN_ENV_PATH', REPO_ROOT / '.env'))
MEMORY_DIR = DATA_DIR / 'memory'
STATE_PATH = MEMORY_DIR / 'predictfun-state.json'
SELL_WATCH_STATE_PATH = MEMORY_DIR / 'predictfun-sell-watch.json'
REPLACE_PLAN_PATH = MEMORY_DIR / 'predictfun-replace-plan.json'
