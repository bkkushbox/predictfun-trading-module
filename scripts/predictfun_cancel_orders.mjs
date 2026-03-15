#!/usr/bin/env node
import fs from 'fs';
import {Wallet} from 'ethers';
import {OrderBuilder, ChainId} from '@predictdotfun/sdk';

const envPath = '/home/alex/.config/openclaw/predictfun.env';
const targetArg = process.argv[2] || 'all';
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

const main = async () => {
  const privateKey = vals.PREDICTFUN_PRIVY_PRIVATE_KEY || vals.PREDICTFUN_PRIVATE_KEY;
  const accountAddress = vals.PREDICTFUN_ACCOUNT_ADDRESS || vals.PREDICTFUN_WALLET_ADDRESS;
  const signer = new Wallet(privateKey);
  const ob = await OrderBuilder.make(ChainId.BnbMainnet, signer, {predictAccount: accountAddress});
  const msgRes = await fetchJson('https://api.predict.fun/v1/auth/message', {headers: {'x-api-key': vals.PREDICTFUN_API_KEY}});
  const message = msgRes?.data?.message;
  const signature = await ob.signPredictAccountMessage(message);
  const jwtRes = await fetchJson('https://api.predict.fun/v1/auth', {method:'POST',headers:{'Content-Type':'application/json','x-api-key':vals.PREDICTFUN_API_KEY},body:JSON.stringify({signer: accountAddress, message, signature})});
  const jwt = jwtRes?.data?.token;
  const privHeaders = {'Authorization':`Bearer ${jwt}`,'x-api-key':vals.PREDICTFUN_API_KEY,'Content-Type':'application/json','User-Agent':'Mozilla/5.0'};
  const openOrders = (await fetchJson('https://api.predict.fun/v1/orders?status=OPEN&first=100', {headers: privHeaders})).data || [];
  const selected = targetArg === 'all' ? openOrders : openOrders.filter((o) => String(o.id) === String(targetArg));
  if (!selected.length) {
    console.log(JSON.stringify({cancelled: 0, target: targetArg, results: []}, null, 2));
    return;
  }
  const ids = selected.map((o) => String(o.id));
  const res = await fetchJson('https://api.predict.fun/v1/orders/remove', {
    method: 'POST',
    headers: privHeaders,
    body: JSON.stringify({data: {ids}}),
  });
  console.log(JSON.stringify({cancelled: ids.length, target: targetArg, ids, response: res}, null, 2));
};

main().catch((err) => { console.error(String(err?.stack || err)); process.exit(1); });
