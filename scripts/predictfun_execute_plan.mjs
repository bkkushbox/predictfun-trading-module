#!/usr/bin/env node
import fs from 'fs';
import {Wallet} from 'ethers';
import {OrderBuilder, ChainId, Side} from '@predictdotfun/sdk';

const [envPath, planPath] = process.argv.slice(2);
if (!envPath || !planPath) {
  console.error('usage: predictfun_execute_plan.mjs <envPath> <planPath>');
  process.exit(2);
}

const loadEnv = (path) => {
  const vals = {};
  for (const raw of fs.readFileSync(path, 'utf8').split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith('#') || !line.includes('=')) continue;
    const idx = line.indexOf('=');
    vals[line.slice(0, idx)] = line.slice(idx + 1);
  }
  return vals;
};

const fetchJson = async (url, options = {}) => {
  const res = await fetch(url, options);
  const text = await res.text();
  let data = {};
  try { data = JSON.parse(text); } catch {}
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${text}`);
  return data;
};
const toJsonSafe = (value) => JSON.parse(JSON.stringify(value, (_, v) => typeof v === 'bigint' ? v.toString() : v));

const main = async () => {
  const vals = loadEnv(envPath);
  const payload = JSON.parse(fs.readFileSync(planPath, 'utf8'));
  const plan = payload.plan || [];
  const signer = new Wallet(vals.PREDICTFUN_PRIVY_PRIVATE_KEY);
  const ob = await OrderBuilder.make(ChainId.BnbMainnet, signer, {predictAccount: vals.PREDICTFUN_ACCOUNT_ADDRESS});

  const msgRes = await fetchJson('https://api.predict.fun/v1/auth/message', {
    headers: {'x-api-key': vals.PREDICTFUN_API_KEY},
  });
  const message = msgRes?.data?.message;
  const signature = await ob.signPredictAccountMessage(message);
  const jwtRes = await fetchJson('https://api.predict.fun/v1/auth', {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'x-api-key': vals.PREDICTFUN_API_KEY},
    body: JSON.stringify({signer: vals.PREDICTFUN_ACCOUNT_ADDRESS, message, signature}),
  });
  const jwt = jwtRes?.data?.token;
  const privHeaders = {
    'Authorization': `Bearer ${jwt}`,
    'x-api-key': vals.PREDICTFUN_API_KEY,
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0',
  };

  const openOrders = (await fetchJson('https://api.predict.fun/v1/orders?status=OPEN&first=100', {headers: privHeaders})).data || [];
  const orderMap = new Map(openOrders.map((o) => [String(o.id), o]));

  const results = [];
  for (const item of plan) {
    const market = (await fetchJson(`https://api.predict.fun/v1/markets/${item.marketId}`, {headers: {'x-api-key': vals.PREDICTFUN_API_KEY, 'User-Agent': 'Mozilla/5.0'}})).data || {};
    for (const act of item.actions || []) {
      const existing = orderMap.get(String(act.cancelOrderId));
      if (!existing) {
        results.push({marketId: item.marketId, side: act.side, cancelled: false, placed: false, skipped: 'order_not_found'});
        continue;
      }

      const cancelRes = await fetchJson('https://api.predict.fun/v1/orders/remove', {
        method: 'POST',
        headers: privHeaders,
        body: JSON.stringify({data: {ids: [String(act.cancelOrderId)]}}),
      });

      if (!cancelRes?.success) {
        results.push({marketId: item.marketId, side: act.side, cancelled: false, placed: false, skipped: 'cancel_failed'});
        continue;
      }

      const side = act.side === 'Yes' ? Side.BUY : Side.BUY;
      const pricePerShareWei = BigInt(Math.round(Number(act.newPrice) * 1e18));
      const quantityWei = BigInt(Math.round(Number(act.newShares) * 1e18));
      const amounts = ob.getLimitOrderAmounts({side, pricePerShareWei, quantityWei});
      const feeRateBps = Number(market.feeRateBps || 0);
      const order = ob.buildOrder('LIMIT', {
        maker: vals.PREDICTFUN_ACCOUNT_ADDRESS,
        signer: vals.PREDICTFUN_ACCOUNT_ADDRESS,
        side,
        tokenId: String(act.tokenId),
        makerAmount: amounts.makerAmount,
        takerAmount: amounts.takerAmount,
        nonce: 0n,
        feeRateBps,
      });
      const typedData = ob.buildTypedData(order, {
        isNegRisk: !!existing.isNegRisk,
        isYieldBearing: !!existing.isYieldBearing,
      });
      const signedOrder = await ob.signTypedDataOrder(typedData);
      const hash = ob.buildTypedDataHash(typedData);
      const createBody = {
        data: {
          order: toJsonSafe({...signedOrder, hash}),
          pricePerShare: amounts.pricePerShare.toString(),
          strategy: 'LIMIT',
        },
      };
      const createRes = await fetchJson('https://api.predict.fun/v1/orders', {
        method: 'POST',
        headers: privHeaders,
        body: JSON.stringify(createBody),
      });
      results.push({
        marketId: item.marketId,
        project: item.project,
        date: item.date,
        side: act.side,
        cancelled: true,
        placed: true,
        newPrice: act.newPrice,
        newShares: act.newShares,
        orderId: createRes?.data?.id || null,
      });
    }
  }

  process.stdout.write(JSON.stringify({results}, null, 2));
};

main().catch((err) => {
  console.error(String(err?.stack || err));
  process.exit(1);
});
