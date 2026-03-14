#!/usr/bin/env python3
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
NODE_HELPER = SCRIPT_DIR / 'predictfun_auth_jwt.mjs'


def get_auth_jwt(api_key: str, predict_account_address: str, privy_private_key: str, log_func=None) -> str:
    cmd = [
        'node',
        str(NODE_HELPER),
        api_key,
        predict_account_address,
        privy_private_key,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        msg = proc.stderr.strip() or proc.stdout.strip() or 'predictfun jwt helper failed'
        raise RuntimeError(msg)
    token = proc.stdout.strip()
    if not token:
        raise RuntimeError('empty jwt token')
    return token


def get_auth_headers(jwt: str, api_key: str) -> dict:
    return {
        'Authorization': f'Bearer {jwt}',
        'x-api-key': api_key,
        'User-Agent': 'Mozilla/5.0',
    }
