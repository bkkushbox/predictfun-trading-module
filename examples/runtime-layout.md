# Runtime Layout

This public package expects a simple local structure.

## Suggested layout

```text
predictfun-trading/
  .env
  data/
    memory/
      predictfun-state.json
      predictfun-sell-watch.json
      predictfun-replace-plan.json
  docs/
  scripts/
  examples/
```

## Environment variables

Optional overrides:
- `PREDICTFUN_ENV_PATH`
- `PREDICTFUN_DATA_DIR`

If you do not set them, the package assumes:
- `.env` in the repository root
- `data/` in the repository root
