#!/usr/bin/env node
import {OrderBuilder, ChainId} from '@predictdotfun/sdk';
import {Wallet} from 'ethers';

const [apiKey, predictAccount, privyKey] = process.argv.slice(2);
if (!apiKey || !predictAccount || !privyKey) {
  console.error('usage: predictfun_auth_jwt.mjs <apiKey> <predictAccount> <privyKey>');
  process.exit(2);
}

const fetchJson = async (url, options = {}) => {
  const res = await fetch(url, options);
  const text = await res.text();
  let data = {};
  try { data = JSON.parse(text); } catch {}
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return data;
};

const main = async () => {
  const signer = new Wallet(privyKey);
  const builder = await OrderBuilder.make(ChainId.BnbMainnet, signer, {
    predictAccount,
  });

  const msgRes = await fetchJson('https://api.predict.fun/v1/auth/message', {
    method: 'GET',
    headers: {
      'x-api-key': apiKey,
    },
  });

  const message = msgRes?.data?.message;
  if (!message) throw new Error('No auth message returned');

  const signature = await builder.signPredictAccountMessage(message);
  const jwtRes = await fetchJson('https://api.predict.fun/v1/auth', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
    },
    body: JSON.stringify({
      signer: predictAccount,
      message,
      signature,
    }),
  });

  const token = jwtRes?.data?.token;
  if (!token) throw new Error('No JWT token returned');
  process.stdout.write(token);
};

main().catch((err) => {
  console.error(String(err?.stack || err));
  process.exit(1);
});
