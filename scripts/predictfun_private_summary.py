#!/usr/bin/env python3
import json, requests, sys, os, io, contextlib
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
try:
    from auth import get_auth_jwt, get_auth_headers
except Exception:
    get_auth_jwt = None
    get_auth_headers = None

ENV_PATH = '/home/alex/.config/openclaw/predictfun.env'
TARGETS_PATH = Path('/home/alex/.openclaw/workspace/docs/PREDICTFUN_TARGET_MARKETS.json')
STATE_PATH = Path('/home/alex/.openclaw/workspace/memory/predictfun-state.json')
API = 'https://api.predict.fun/v1'
BUDGET = 118.0


def load_env():
    vals={}
    for line in open(ENV_PATH):
        line=line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k,v=line.split('=',1)
        vals[k]=v
    return vals


def get_json(url, headers=None, params=None):
    r=requests.get(url, headers=headers, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def first_level(side):
    if isinstance(side, list) and side:
        row=side[0]
        if isinstance(row,list) and len(row)>=2:
            return float(row[0]), float(row[1])
    return 0.0,0.0


def cents(x):
    return round(x*100,1)


def fmt_order(order):
    if not order:
        return 'нет'
    return f"{cents(order['price']):.1f}¢ ({round(order['shares'],2):.2f} shares)"


def main():
    if get_auth_jwt is None or get_auth_headers is None:
        return
    if STATE_PATH.exists():
        try:
            state = json.loads(STATE_PATH.read_text())
            if state.get('mode') == 'SELL_HOLD_MODE':
                return
        except Exception:
            pass
    vals=load_env()
    with contextlib.redirect_stdout(io.StringIO()):
        jwt=get_auth_jwt(vals['PREDICTFUN_API_KEY'], vals['PREDICTFUN_ACCOUNT_ADDRESS'], vals['PREDICTFUN_PRIVY_PRIVATE_KEY'], log_func=lambda *a, **k: None)
    priv_headers=get_auth_headers(jwt, vals['PREDICTFUN_API_KEY'])
    pub_headers={'x-api-key':vals['PREDICTFUN_API_KEY'],'User-Agent':'Mozilla/5.0'}
    targets=json.loads(TARGETS_PATH.read_text())
    orders=get_json(f'{API}/orders', priv_headers, {'status':'OPEN','first':'100'}).get('data',[])

    market_map={}
    order_map=defaultdict(dict)
    for project,cfg in targets.items():
        for tm in cfg['markets']:
            mid=tm['id']
            m=get_json(f'{API}/markets/{mid}', pub_headers).get('data',{})
            ob=get_json(f'{API}/markets/{mid}/orderbook', pub_headers).get('data',{})
            bid,_=first_level(ob.get('bids'))
            ask,_=first_level(ob.get('asks'))
            yes=ask if ask else 0.0
            no=max(1-bid, 0.0) if bid else 0.0
            spread=max(ask-bid,0)
            market_map[mid]={
                'project': project,
                'date': str(m.get('title') or '').replace('?',''),
                'yes': yes,
                'no': no,
                'spread': spread,
                'outcomes': {str(o.get('onChainId')): o.get('name') for o in m.get('outcomes',[])}
            }

    for o in orders:
        mid=o.get('marketId')
        if mid not in market_map:
            continue
        tok=str(o.get('order',{}).get('tokenId',''))
        outcome=market_map[mid]['outcomes'].get(tok)
        if not outcome:
            continue
        maker=float(o.get('order',{}).get('makerAmount','0'))/1e18
        taker=float(o.get('order',{}).get('takerAmount','0'))/1e18
        side=o.get('side', o.get('order',{}).get('side'))
        # BUY: maker=стоимость, taker=shares => price = maker/taker
        # SELL: maker=shares, taker=стоимость => price = taker/maker
        if maker and taker:
            price = (maker/taker) if side in (0, '0', 'BUY', 'buy') else (taker/maker)
        else:
            price = 0.0
        shares = taker if side in (0, '0', 'BUY', 'buy') else maker
        order_map[mid][outcome]={'price':price,'shares':shares,'orderId':o.get('id')}

    date_rank = {
        'June 30, 2026': 1,
        'September 30, 2026': 2,
        'December 31, 2026': 3,
        'March 31, 2026': 0,
    }

    blocks=[]
    for mid,info in sorted(market_map.items(), key=lambda kv: (kv[1]['project'], date_rank.get(kv[1]['date'], 99), kv[1]['date'])):
        yes_w=max(info['yes']-0.03,0.001)
        no_w=max(info['no']-0.03,0.001)
        yes_sh=BUDGET/yes_w
        no_sh=BUDGET/no_w
        my_yes=order_map[mid].get('Yes')
        my_no=order_map[mid].get('No')

        # treat missing order as current market-side visibility if user wants concise line
        current_yes_order = f"{cents(my_yes['price']):.1f}¢" if my_yes else 'нет'
        current_no_order = f"{cents(my_no['price']):.1f}¢" if my_no else 'нет'

        yes_action = '✅ без изменений'
        if my_yes and abs(my_yes['price']-yes_w) >= 0.005:
            yes_action = f"🔄 переставить на {cents(yes_w):.1f}¢ ({yes_sh:.2f} shares)"
        no_action = '✅ без изменений'
        if my_no and abs(my_no['price']-no_w) >= 0.005:
            no_action = f"🔄 переставить на {cents(no_w):.1f}¢ ({no_sh:.2f} shares)"

        block = (
            f"**{info['project']} ({info['date']})**\n"
            f"• рынок: Yes {cents(info['yes']):.1f}¢, No {cents(info['no']):.1f}¢, spread {cents(info['spread']):.1f}¢\n"
            f"• твои ордера: Yes {current_yes_order}, No {current_no_order}\n\n"
            f"**Что сделать:**\n"
            f"• **Yes** — {yes_action}\n"
            f"• **No** — {no_action}"
        )
        blocks.append(block)

    print('\n\n'.join(blocks))

if __name__ == '__main__':
    main()
