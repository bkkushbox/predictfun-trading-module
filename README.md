# PredictFun Trading Module

PredictFun Trading Module is a semi-automatic trading workflow for PredictFun with strict user confirmation for all trading actions. The module monitors private orders, handles pause logic after a fill, tracks sell orders, places and replaces buy orders, and keeps notifications short and operational.

## What the module does

The module monitors private open orders and market state, detects fills, enters `SELL_HOLD_MODE`, watches the active sell order, and waits for user instructions after the sell is no longer active. It can place `Yes + No` buy orders, propose order replacement when market conditions move, execute replacements only after explicit user confirmation, and cancel one or all buy orders through the correct private API flow.

## Confirmed working behaviors

This module has been confirmed in live tests for the following flows:

- placing a single buy order;
- placing `Yes + No` buy orders;
- replacing `Yes + No` orders after explicit confirmation;
- cancelling test buy orders;
- keeping the active sell order untouched during buy-order cleanup;
- using the correct cancel flow through `POST /v1/orders/remove`.

## Core rules

All trading actions are confirmation-gated. The module may monitor, calculate, and notify without confirmation, but it must not place, replace, or cancel trading orders without explicit user approval.

## Main runtime flow

### Normal buy mode

The private summary checks market state and private open orders. The trigger check runs on schedule and decides whether a replacement is needed. If the existing buy orders are already aligned with the target rules, the module returns `NO_CHANGES`. If a replacement is needed, the module sends a short proposal and waits for user confirmation before executing it.

### Fill happened

After a buy order is filled, the module enters `SELL_HOLD_MODE`. It sends one pause notification and then stays quiet instead of repeating the same message every hour.

### Sell order active

When the user places a sell order, the module detects it in private open orders and sends a sell message in the fixed format. After that, it monitors the order quietly.

### Sell order no longer active

When the sell order disappears from open orders, the module sends a short status update and waits for one of two user commands:
- `выстави сам`
- `ордера выставил сам`

If the user says `выстави сам`, the module places fresh `Yes + No` buy orders according to the configured rules. If the user says `ордера выставил сам`, the module scans the already placed buy orders and resumes monitoring and replace proposals.

## Repository structure

- `docs/` – architecture, operations, implementation stages, target markets
- `scripts/` – auth, monitoring, place, replace, cancel, execution, message senders
- `examples/` – reserved for public examples and sample payloads

## Files to read first

- `docs/PREDICTFUN_OPERATIONS.md`
- `docs/PREDICTFUN_ARCHITECTURE.md`
- `QUICKSTART.md`
- `SECURITY.md`
- `examples/predictfun.env.example`
- `examples/runtime-layout.md`

## Important technical note

The correct cancel flow for the Predict account is:

- `POST /v1/orders/remove`

Do not assume SDK `cancelOrders()` matches the real UX or production workflow.

## Status

This repository is designed to be publish-ready after secret cleanup and per-user configuration replacement. All runtime credentials must be supplied by the operator and are not included in the repository.
