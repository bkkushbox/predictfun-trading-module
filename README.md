# PredictFun Trading Module

A semi-automatic PredictFun trading module with private order monitoring, `SELL_HOLD_MODE`, confirmation-gated order placement, confirmation-gated replace flow, and operational notifications in a fixed format.

## What this repository gives you

This repository contains a working operational module for PredictFun trading workflows. It is designed for an operator who wants monitoring and execution help without giving full autonomy to the bot. The module watches private open orders, reacts correctly after a fill, tracks the active sell order, places fresh `Yes + No` buy orders after explicit confirmation, proposes replacements when prices move, and executes replacements only after the user confirms.

## Core principles

- Monitoring can run automatically.
- Trading actions stay confirmation-gated.
- After a fill, the module enters `SELL_HOLD_MODE`.
- In `SELL_HOLD_MODE`, the module sends one pause notification and then stays quiet.
- Sell orders are monitored silently until their status changes.
- Buy-order placement, replacement, and cancel-all require explicit user approval.

## Confirmed in live tests

The following behaviors have already been confirmed in production tests:

- place one buy order;
- place `Yes + No` buy orders;
- replace `Yes + No` after explicit confirmation;
- cancel test buy orders;
- keep the active sell order untouched during buy cleanup;
- use the correct private cancel flow through `POST /v1/orders/remove`.

## Main runtime flow

### 1. Normal buy mode

The module monitors market state and private open orders. If current orders still match the target rules, it returns `NO_CHANGES`. If a replacement is needed, it sends a proposal and waits for explicit confirmation before executing it.

### 2. After a fill

The module enters `SELL_HOLD_MODE` and sends one pause notification. After that, it does not spam repeated hourly messages.

### 3. Sell order active

When the user places a sell order, the module detects it and sends a sell notification in a fixed operational format. Then it continues to monitor silently.

### 4. Sell order no longer active

When the sell order disappears from open orders, the module sends a short status message and waits for one of two user commands:
- `выстави сам`
- `ордера выставил сам`

### 5. Replace flow

If the user wants the module to manage the buy side, the module can place fresh `Yes + No` buy orders. If the market moves, it builds a replace plan, sends a proposal, and executes the replace only after confirmation.

## Repository structure

```text
predictfun-trading-module/
  README.md
  QUICKSTART.md
  SECURITY.md
  PUBLISHING_NOTES.md
  docs/
  examples/
  scripts/
```

## Read these files first

- `QUICKSTART.md` – how to get running quickly
- `SECURITY.md` – what must stay private
- `docs/PREDICTFUN_OPERATIONS.md` – full runtime logic and output behavior
- `docs/PREDICTFUN_ARCHITECTURE.md` – architecture and module layers
- `examples/predictfun.env.example` – env template
- `examples/runtime-layout.md` – suggested local folder layout

## Important technical note

The correct cancel path for the Predict account is:

- `POST /v1/orders/remove`

Do not assume SDK `cancelOrders()` matches the real production UX.

## Status

This repository is publish-ready as a sanitized public package. Real credentials, live environment files, JWT tokens, cookies, and operational secrets are intentionally excluded.
