#!/usr/bin/env python3
import json, requests, sys, hashlib, io, contextlib
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from auth import get_auth_jwt, get_auth_headers

BUDGET=118.0
TRIGGER=0.02
API='https://api.predict.fun/v1'
ENV_PATH='/home/alex/.config/openclaw/predictfun.env'
TARGETS_PATH=Path('/home/alex/.openclaw/workspace/docs/PREDICTFUN_TARGET_MARKETS.json')
STATE_PATH=Path('/home/alex/.openclaw/workspace/memory/predictfun-trigger-state.json')
MODE_PATH=Path('/home/alex/.openclaw/workspace/memory/predictfun-state.json')


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
    r.raise_for_status(); return r.json()


def first_level(side):
    if isinstance(side, list) and side:
        row=side[0]
        if isinstance(row,list) and len(row)>=2:
            return float(row[0]), float(row[1])
    return 0.0,0.0


def cents(x):
    return round(x*100,1)


def main():
    if MODE_PATH.exists():
        try:
            mode = json.loads(MODE_PATH.read_text())
            if mode.get('mode') == 'SELL_HOLD_MODE':
                print(json.dumps({'message':'', 'send':False, 'digest':''}, ensure_ascii=False))
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
            no=max(1-bid,0.0) if bid else 0.0
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
        price=taker/maker if maker else 0.0
        order_map[mid][outcome]={'price':price,'shares':taker}

    alerts=[]
    for mid,info in market_map.items():
        yes_target=max(info['yes']-0.03,0.001)
        no_target=max(info['no']-0.03,0.001)
        yes_sh=BUDGET/yes_target
        no_sh=BUDGET/no_target
        my_yes=order_map[mid].get('Yes')
        my_no=order_map[mid].get('No')
        yes_action=None
        no_action=None
        if my_yes and abs(my_yes['price']-yes_target) >= TRIGGER:
            yes_action=f"• **Yes** — 🔄 переставить на {cents(yes_target):.1f}¢ ({yes_sh:.2f} shares)"
        if my_no and abs(my_no['price']-no_target) >= TRIGGER:
            no_action=f"• **No** — 🔄 переставить на {cents(no_target):.1f}¢ ({no_sh:.2f} shares)"
        if yes_action or no_action:
            lines=[
                f"**{info['project']} ({info['date']})**",
                f"• рынок: Yes {cents(info['yes']):.1f}¢, No {cents(info['no']):.1f}¢, spread {cents(info['spread']):.1f}¢",
                f"• твои ордера: Yes {cents(my_yes['price']):.1f}¢" + (f", No {cents(my_no['price']):.1f}¢" if my_no else ', No нет') if my_yes else (f"• твои ордера: Yes нет, No {cents(my_no['price']):.1f}¢" if my_no else '• твои ордера: Yes нет, No нет'),
                '❗️**Что сделать:**'
            ]
            if yes_action:
                lines.append(yes_action)
            if no_action:
                lines.append(no_action)
            alerts.append('\n'.join(lines))

    msg='\n\n'.join(alerts).strip()
    digest=hashlib.sha256(msg.encode()).hexdigest() if msg else ''
    prev=''
    if STATE_PATH.exists():
        try:
            prev=json.loads(STATE_PATH.read_text()).get('last_digest','')
        except Exception:
            prev=''
    out={'message': msg, 'send': bool(msg and digest != prev), 'digest': digest}
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps({'last_digest': digest}, ensure_ascii=False))
    print(json.dumps(out, ensure_ascii=False))

if __name__ == '__main__':
    main()
