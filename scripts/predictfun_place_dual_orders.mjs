#!/usr/bin/env node
import fs from 'fs';
import {Wallet} from 'ethers';
import {OrderBuilder, ChainId, Side} from '@predictdotfun/sdk';

const marketId = Number(process.argv[2]);
const budget = Number(process.argv[3] || '1');
if (!marketId || !budget) {
  console.error('usage: predictfun_place_dual_orders.mjs <marketId> <budgetUsdPerSide>');
  process.exit(2);
}
const envPath = '/home/alex/.config/openclaw/predictfun.env';
const vals = {};
for (const raw of fs.readFileSync(envPath, 'utf8').split(/\r?\n/)) {
  const line = raw.trim();
  if (!line || line.startsWith('#') || !line.includes('=')) continue;
  const idx = line.indexOf('=');
  vals[line.slice(0, idx)] = line.slice(idx + 1);
}
const fetchJson = async (url, options = {}) => {
  const res = await fetch(url, options);
  const text = await res.text();
  let data = {};
  try { data = JSON.parse(text); } catch {}
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${text}`);
  return data;
};
const createOne = async (ob, headers, market, sideName, tokenId, target, budget) => {
  const side = Side.BUY;
  const quantity = budget / target;
  const pricePerShareWei = BigInt(Math.round(target * 1e18));
  const quantityWei = BigInt(Math.round(quantity * 1e18));
  const amounts = ob.getLimitOrderAmounts({side, pricePerShareWei, quantityWei});
  const order = ob.buildOrder('LIMIT', {
    maker: accountAddress,
    signer: accountAddress,
    side,
    tokenId: String(tokenId),
    makerAmount: amounts.makerAmount,
    takerAmount: amounts.takerAmount,
    nonce: 0n,
    feeRateBps: Number(market.feeRateBps || 0),
  });
  const typedData = ob.buildTypedData(order, {isNegRisk: false, isYieldBearing: false});
  const signedOrder = await ob.signTypedDataOrder(typedData);
  const hash = ob.buildTypedDataHash(typedData);
  const createRes = await fetchJson('https://api.predict.fun/v1/orders', {
    method:'POST',
    headers,
    body: JSON.stringify({data:{order:{...signedOrder, hash}, pricePerShare: amounts.pricePerShare.toString(), strategy:'LIMIT'}})
  });
  return {side: sideName, target, quantity, id: createRes?.data?.id || null};
};
const main = async () => {
  const privateKey = vals.PREDICTFUN_PRIVY_PRIVATE_KEY || vals.PREDICTFUN_PRIVATE_KEY;
  const accountAddress = vals.PREDICTFUN_ACCOUNT_ADDRESS || vals.PREDICTFUN_WALLET_ADDRESS;
  const signer = new Wallet(privateKey);
  const ob = await OrderBuilder.make(ChainId.BnbMainnet, signer, {predictAccount: accountAddress});
  await ob.setApprovals();
  const msgRes = await fetchJson('https://api.predict.fun/v1/auth/message', {headers: {'x-api-key': vals.PREDICTFUN_API_KEY}});
  const signature = await ob.signPredictAccountMessage(msgRes.data.message);
  const jwtRes = await fetchJson('https://api.predict.fun/v1/auth', {method:'POST', headers:{'Content-Type':'application/json','x-api-key':vals.PREDICTFUN_API_KEY}, body: JSON.stringify({signer: accountAddress, message: msgRes.data.message, signature})});
  const jwt = jwtRes.data.token;
  const privHeaders = {'Authorization': `Bearer ${jwt}`, 'x-api-key': vals.PREDICTFUN_API_KEY, 'Content-Type':'application/json', 'User-Agent':'Mozilla/5.0'};
  const pubHeaders = {'x-api-key': vals.PREDICTFUN_API_KEY, 'User-Agent':'Mozilla/5.0'};
  const market = (await fetchJson(`https://api.predict.fun/v1/markets/${marketId}`, {headers: pubHeaders})).data;
  const book = (await fetchJson(`https://api.predict.fun/v1/markets/${marketId}/orderbook`, {headers: pubHeaders})).data;
  const bid = book?.bids?.length ? Number(book.bids[0][0]) : 0;
  const ask = book?.asks?.length ? Number(book.asks[0][0]) : 0;
  const yesTarget = Math.max(ask - 0.03, 0.001);
  const noTarget = Math.max((1 - bid) - 0.03, 0.001);
  const yesOutcome = (market.outcomes || []).find((o) => o.name === 'Yes');
  const noOutcome = (market.outcomes || []).find((o) => o.name === 'No');
  const yesRes = await createOne(ob, privHeaders, market, 'Yes', yesOutcome.onChainId, yesTarget, budget);
  const noRes = await createOne(ob, privHeaders, market, 'No', noOutcome.onChainId, noTarget, budget);
  console.log(JSON.stringify({project: 'MetaMask', date: market.title, marketId, ask, bid, yesTarget, noTarget, budget, results:[yesRes,noRes]}, null, 2));
};
main().catch((err)=>{console.error(String(err?.stack || err));process.exit(1);});
