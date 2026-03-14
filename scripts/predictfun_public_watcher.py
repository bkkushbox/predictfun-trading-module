#!/usr/bin/env python3
import json, os, requests
from pathlib import Path
from datetime import datetime, timezone

ENV_PATH = '/home/alex/.config/openclaw/predictfun.env'
TARGETS_PATH = Path('/home/alex/.openclaw/workspace/docs/PREDICTFUN_TARGET_MARKETS.json')
STATE_PATH = Path('/home/alex/.openclaw/workspace/memory/predictfun-public-state.json')
API = 'https://api.predict.fun/v1'
HEADERS = {'User-Agent': 'Mozilla/5.0 (OpenClaw PredictFun Public Watcher)'}
SIGNIFICANT_LAST_SALE = 0.03
SIGNIFICANT_VOLUME_ABS = 500.0
SIGNIFICANT_VOLUME_REL = 0.30
SIGNIFICANT_SPREAD_CHANGE = 0.03
SIGNIFICANT_TOP_BOOK_CHANGE = 0.03


def load_key():
    if not os.path.exists(ENV_PATH):
        return None
    for line in open(ENV_PATH):
        if line.startswith('PREDICTFUN_API_KEY='):
            return line.split('=', 1)[1].strip()
    return None


def api_get(path, key):
    headers = dict(HEADERS)
    if key:
        headers['x-api-key'] = key
    r = requests.get(f'{API}{path}', headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()


def load_targets():
    return json.loads(TARGETS_PATH.read_text())


def first_level(side):
    if isinstance(side, list) and side:
        row = side[0]
        if isinstance(row, list) and len(row) >= 2:
            return float(row[0]), float(row[1])
    return 0.0, 0.0


def get_market_snapshot(market_id, key):
    market = api_get(f'/markets/{market_id}', key).get('data', {})
    stats = api_get(f'/markets/{market_id}/stats', key).get('data', {})
    last_sale = api_get(f'/markets/{market_id}/last-sale', key).get('data', {})
    orderbook = api_get(f'/markets/{market_id}/orderbook', key).get('data', {})

    best_ask_price, best_ask_size = first_level(orderbook.get('asks'))
    best_bid_price, best_bid_size = first_level(orderbook.get('bids'))
    return {
        'id': market.get('id'),
        'title': market.get('title') or '',
        'question': market.get('question') or '',
        'categorySlug': market.get('categorySlug') or '',
        'conditionId': market.get('conditionId') or '',
        'status': market.get('status') or '',
        'tradingStatus': market.get('tradingStatus') or '',
        'lastSaleOutcome': last_sale.get('outcome') or '',
        'lastSalePrice': float(str(last_sale.get('priceInCurrency') or '0')) / 1e18,
        'lastSaleQuoteType': last_sale.get('quoteType') or '',
        'volume24hUsd': float(stats.get('volume24hUsd') or 0),
        'volumeTotalUsd': float(stats.get('volumeTotalUsd') or 0),
        'totalLiquidityUsd': float(stats.get('totalLiquidityUsd') or 0),
        'bestBid': best_bid_price,
        'bestBidSize': best_bid_size,
        'bestAsk': best_ask_price,
        'bestAskSize': best_ask_size,
        'spread': max(best_ask_price - best_bid_price, 0),
    }


def detect_changes(prev, cur, project):
    alerts = []
    prev_map = {str(x.get('id')): x for x in prev}
    for m in cur:
        old = prev_map.get(str(m.get('id')))
        if not old:
            continue
        changes = []
        old_ls = float(old.get('lastSalePrice') or 0)
        new_ls = float(m.get('lastSalePrice') or 0)
        if old_ls > 0 and abs(new_ls - old_ls) >= SIGNIFICANT_LAST_SALE:
            changes.append(f'цена последней сделки изменилась с {old_ls:.3f} до {new_ls:.3f}')

        old_v = float(old.get('volume24hUsd') or 0)
        new_v = float(m.get('volume24hUsd') or 0)
        if ((new_v - old_v) >= SIGNIFICANT_VOLUME_ABS) or (old_v > 0 and new_v > old_v * (1 + SIGNIFICANT_VOLUME_REL)):
            changes.append(f'24ч объём изменился с ${old_v:.0f} до ${new_v:.0f}')

        old_spread = float(old.get('spread') or 0)
        new_spread = float(m.get('spread') or 0)
        if abs(new_spread - old_spread) >= SIGNIFICANT_SPREAD_CHANGE:
            changes.append(f'спред изменился с {old_spread:.3f} до {new_spread:.3f}')

        old_bid = float(old.get('bestBid') or 0)
        new_bid = float(m.get('bestBid') or 0)
        old_ask = float(old.get('bestAsk') or 0)
        new_ask = float(m.get('bestAsk') or 0)
        if abs(new_bid - old_bid) >= SIGNIFICANT_TOP_BOOK_CHANGE or abs(new_ask - old_ask) >= SIGNIFICANT_TOP_BOOK_CHANGE:
            changes.append(f'верх стакана изменился: bid {old_bid:.3f}->{new_bid:.3f}, ask {old_ask:.3f}->{new_ask:.3f}')

        if changes:
            importance = 'средний'
            if len(changes) >= 3 or ('24ч объём' in ' '.join(changes) and 'цена последней сделки' in ' '.join(changes)):
                importance = 'высокий'
            if len(changes) >= 4:
                importance = 'очень сильный'
            alerts.append({
                'project': project,
                'title': m.get('question') or m.get('title') or project,
                'changes': changes,
                'importance': importance,
            })
    return alerts


def main():
    key = load_key()
    targets = load_targets()
    grouped = {}
    for project, cfg in targets.items():
        grouped[project] = []
        for item in cfg.get('markets', []):
            market = get_market_snapshot(item['id'], key)
            market['kind'] = item.get('kind')
            market['source'] = cfg.get('source', 'category')
            grouped[project].append(market)

    old = {k: [] for k in grouped}
    if STATE_PATH.exists():
        try:
            old = json.loads(STATE_PATH.read_text())
        except Exception:
            pass

    alerts = []
    for project in grouped:
        alerts.extend(detect_changes(old.get(project, []), grouped[project], project))

    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(grouped, ensure_ascii=False))
    print(json.dumps({'generated_at': datetime.now(timezone.utc).isoformat(), 'alerts': alerts, 'markets': grouped}, ensure_ascii=False))

if __name__ == '__main__':
    main()
