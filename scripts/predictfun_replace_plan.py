#!/usr/bin/env python3
import json, requests, sys, io, contextlib
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timezone

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
try:
    from auth import get_auth_jwt, get_auth_headers
except Exception:
    get_auth_jwt = None
    get_auth_headers = None

BUDGET=118.0
TRIGGER=0.02
API='https://api.predict.fun/v1'
ENV_PATH='/home/alex/.config/openclaw/predictfun.env'
TARGETS_PATH=Path('/home/alex/.openclaw/workspace/docs/PREDICTFUN_TARGET_MARKETS.json')
PLAN_PATH=Path('/home/alex/.openclaw/workspace/memory/predictfun-replace-plan.json')
MODE_PATH=Path('/home/alex/.openclaw/workspace/memory/predictfun-state.json')


def load_env():
    vals={}
    for line in open(ENV_PATH):
        line=line.strip()
        if not line or line.startswith('#') or '=' not in line: continue
        k,v=line.split('=',1); vals[k]=v
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
    if get_auth_jwt is None or get_auth_headers is None:
        print('NO_CHANGES')
        return
    if MODE_PATH.exists():
        try:
            mode = json.loads(MODE_PATH.read_text())
            if mode.get('mode') == 'SELL_HOLD_MODE':
                print('NO_CHANGES')
                return
        except Exception:
            pass
    vals=load_env()
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            jwt=get_auth_jwt(vals['PREDICTFUN_API_KEY'], vals['PREDICTFUN_ACCOUNT_ADDRESS'], vals['PREDICTFUN_PRIVY_PRIVATE_KEY'], log_func=lambda *a, **k: None)
        priv_headers=get_auth_headers(jwt, vals['PREDICTFUN_API_KEY'])
        pub_headers={'x-api-key':vals['PREDICTFUN_API_KEY'],'User-Agent':'Mozilla/5.0'}
        targets=json.loads(TARGETS_PATH.read_text())
        orders=get_json(f'{API}/orders', priv_headers, {'status':'OPEN','first':'100'}).get('data',[])
    except Exception:
        print('NO_CHANGES')
        return
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
                'yes': yes, 'no': no, 'spread': spread,
                'outcomes': {str(o.get('onChainId')): o.get('name') for o in m.get('outcomes',[])}
            }
    for o in orders:
        mid=o.get('marketId')
        if mid not in market_map: continue
        tok=str(o.get('order',{}).get('tokenId',''))
        outcome=market_map[mid]['outcomes'].get(tok)
        if not outcome: continue
        maker=float(o.get('order',{}).get('makerAmount','0'))/1e18
        taker=float(o.get('order',{}).get('takerAmount','0'))/1e18
        side=o.get('side', o.get('order',{}).get('side'))
        if maker and taker:
            price = (maker/taker) if side in (0, '0', 'BUY', 'buy') else (taker/maker)
        else:
            price = 0.0
        shares = taker if side in (0, '0', 'BUY', 'buy') else maker
        order_map[mid][outcome]={'price':price,'shares':shares,'orderId':o.get('id')}

    plan=[]
    blocks=[]
    for mid,info in sorted(market_map.items(), key=lambda kv: (kv[1]['project'], kv[1]['date'])):
        yes_target=max(info['yes']-0.03,0.001)
        no_target=max(info['no']-0.03,0.001)
        yes_sh=round(BUDGET/yes_target,2)
        no_sh=round(BUDGET/no_target,2)
        my_yes=order_map[mid].get('Yes')
        my_no=order_map[mid].get('No')
        actions=[]
        text_actions=[]
        if my_yes and abs(my_yes['price']-yes_target) >= TRIGGER:
            actions.append({'side':'Yes','cancelOrderId':my_yes['orderId'],'newPrice':round(yes_target,4),'newShares':yes_sh,'tokenId': next((k for k,v in info['outcomes'].items() if v == 'Yes'), None)})
            text_actions.append(f"• **Yes** — 🔄 переставить на {cents(yes_target):.1f}¢ ({yes_sh:.2f} shares)")
        if my_no and abs(my_no['price']-no_target) >= TRIGGER:
            actions.append({'side':'No','cancelOrderId':my_no['orderId'],'newPrice':round(no_target,4),'newShares':no_sh,'tokenId': next((k for k,v in info['outcomes'].items() if v == 'No'), None)})
            text_actions.append(f"• **No** — 🔄 переставить на {cents(no_target):.1f}¢ ({no_sh:.2f} shares)")
        if actions:
            plan.append({
                'marketId': mid,
                'project': info['project'],
                'date': info['date'],
                'actions': actions
            })
            yes_txt = f"{cents(my_yes['price']):.1f}¢" if my_yes else 'нет'
            no_txt = f"{cents(my_no['price']):.1f}¢" if my_no else 'нет'
            blocks.append(
                f"**{info['project']} ({info['date']})**\n"
                f"• рынок: Yes {cents(info['yes']):.1f}¢, No {cents(info['no']):.1f}¢, spread {cents(info['spread']):.1f}¢\n"
                f"• твои ордера: Yes {yes_txt}, No {no_txt}\n"
                f"❗️**Что сделать:**\n" + '\n'.join(text_actions)
            )
    payload={'generatedAt': datetime.now(timezone.utc).isoformat(), 'budgetPerSide': BUDGET, 'triggerCents': 2, 'plan': plan}
    PLAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    PLAN_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    if blocks:
        print("\n\n".join(blocks) + "\n\n**Подтвердить переставление?**")
    else:
        print('NO_CHANGES')

if __name__ == '__main__':
    main()
