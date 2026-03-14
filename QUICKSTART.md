# Quick Start

## 1. Provide your own credentials

Create a local environment file named `.env` in the repository root based on `examples/predictfun.env.example` and fill in your own values:

- `PREDICTFUN_API_KEY`
- `PREDICTFUN_ACCOUNT_ADDRESS`
- `PREDICTFUN_PRIVY_PRIVATE_KEY`

Do not commit the real environment file.

## 2. Install runtime dependencies

The JavaScript helper scripts require:
- Node.js
- npm
- `@predictdotfun/sdk`
- `ethers`

The Python scripts require:
- Python 3
- `requests`

## 3. Verify auth

Run the auth layer first and make sure JWT generation works before attempting private order monitoring or trading actions.

## 4. Verify private read-only flow

Test:
- private summary
- trigger check
- sell watch

These checks should run without trading actions.

## 5. Enable trading actions only after confirmation policy is clear

Trading actions should be used only after the operator confirms the rules:
- placing orders;
- replacing orders;
- cancelling all buy orders.

## 6. Main commands

Examples:
- place dual buy orders:
  - `node scripts/predictfun_place_dual_orders.mjs <marketId> <budgetUsdPerSide>`
- cancel one or all:
  - `node scripts/predictfun_cancel_orders.mjs <orderId|all>`
- execute saved replace plan:
  - `python3 scripts/predictfun_execute_pending.py`

## 7. Keep notification formats stable

Use the formats documented in `docs/PREDICTFUN_OPERATIONS.md` and keep messages short, operational, and confirmation-gated.
