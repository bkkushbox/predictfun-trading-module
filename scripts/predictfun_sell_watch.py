#!/usr/bin/env python3
import io
import json
import contextlib
from pathlib import Path
import requests
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from auth import get_auth_jwt, get_auth_headers
from predictfun_paths import ENV_PATH, STATE_PATH as MODE_PATH, SELL_WATCH_STATE_PATH as WATCH_STATE_PATH
API = 'https://api.predict.fun/v1'


def load_env():
    vals = {}
    for line in open(ENV_PATH):
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        vals[k] = v
    return vals


def get_json(url, headers=None, params=None):
    r = requests.get(url, headers=headers, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def load_json(path, default):
    try:
        return json.loads(path.read_text()) if path.exists() else default
    except Exception:
        return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def first_level(side):
    if isinstance(side, list) and side:
        row = side[0]
        if isinstance(row, list) and len(row) >= 2:
            return float(row[0]), float(row[1])
    return 0.0, 0.0


def cents(x):
    return round(float(x) * 100, 1)


def fmt_price_from_order(order_obj):
    order = order_obj.get('order', {})
    maker = float(order.get('makerAmount', '0')) / 1e18
    taker = float(order.get('takerAmount', '0')) / 1e18
    if maker <= 0:
        return 'нет'
    price = taker / maker
    return f"{cents(price):.1f}¢"


def build_sell_pause_message(sell_order, headers):
    market_id = sell_order.get('marketId')
    market = get_json(f'{API}/markets/{market_id}', headers).get('data', {})
    orderbook = get_json(f'{API}/markets/{market_id}/orderbook', headers).get('data', {})
    bid, _ = first_level(orderbook.get('bids'))
    ask, _ = first_level(orderbook.get('asks'))
    yes = ask if ask else 0.0
    no = max(1 - bid, 0.0) if bid else 0.0
    spread = max(ask - bid, 0.0) if ask and bid else 0.0
    sell_price = fmt_price_from_order(sell_order)
    title = str(market.get('title') or market_id).replace('?', '')
    return '\n'.join([
        f"**{title}**",
        f"• рынок: Yes {cents(yes):.1f}¢, No {cents(no):.1f}¢, spread {cents(spread):.1f}¢",
        f"• твои ордера: Sell {sell_price} (id {sell_order.get('id')})",
        '❗️**Что делать:**',
        '• **Sell** — ордер на продаже активен, модуль на паузе и ждёт исполнения.',
    ])


def main():
    mode = load_json(MODE_PATH, {})
    if mode.get('mode') != 'SELL_HOLD_MODE':
        print('NO_EVENT')
        return

    vals = load_env()
    with contextlib.redirect_stdout(io.StringIO()):
        jwt = get_auth_jwt(vals['PREDICTFUN_API_KEY'], vals['PREDICTFUN_ACCOUNT_ADDRESS'], vals['PREDICTFUN_PRIVY_PRIVATE_KEY'])
    headers = get_auth_headers(jwt, vals['PREDICTFUN_API_KEY'])
    orders = get_json(f'{API}/orders', headers, {'status': 'OPEN', 'first': '100'}).get('data', [])

    sell_orders = []
    for o in orders:
        order = o.get('order', {})
        side = o.get('side', order.get('side'))
        # В Predict SDK Side.BUY=0, Side.SELL=1. Держим и строковые, и numeric варианты.
        if side in (1, '1', 'SELL', 'sell'):
            sell_orders.append(o)

    prev = load_json(WATCH_STATE_PATH, {'pauseNotified': False, 'lastOpenSellCount': None, 'lastResolved': None})

    if sell_orders:
        current_ids = [str(o.get('id')) for o in sell_orders if o.get('id') is not None]
        if not prev.get('pauseNotified'):
            save_json(WATCH_STATE_PATH, {
                'pauseNotified': True,
                'lastOpenSellCount': len(sell_orders),
                'lastOpenSellIds': current_ids,
                'lastResolved': None,
            })
            print(build_sell_pause_message(sell_orders[0], headers))
            return
        save_json(WATCH_STATE_PATH, {
            'pauseNotified': True,
            'lastOpenSellCount': len(sell_orders),
            'lastOpenSellIds': current_ids,
            'lastResolved': None,
        })
        print('NO_EVENT')
        return

    if prev.get('pauseNotified') and prev.get('lastResolved') != 'sell_filled_or_closed':
        last_ids = ', '.join(prev.get('lastOpenSellIds', [])) or 'нет id'
        save_json(WATCH_STATE_PATH, {
            'pauseNotified': True,
            'lastOpenSellCount': 0,
            'lastOpenSellIds': [],
            'lastResolved': 'sell_filled_or_closed',
        })
        print('\n'.join([
            '**PredictFun — sell-ордер**',
            f'• рынок: sell-ордер больше не активен',
            f'• твои ордера: Sell id {last_ids} закрыт/исполнен',
            '❗️**Что делать:**',
            '• **Sell** — проверь исполнение и реши: выставить всё заново или оставить решение себе.',
        ]))
        return

    print('NO_EVENT')


if __name__ == '__main__':
    main()
