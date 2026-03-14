# Security Notes

## What must stay private

Never publish:
- real API keys;
- real private keys;
- real JWT tokens;
- real auth headers;
- real cookies;
- production-only internal paths that expose secrets.

## Environment handling

All runtime credentials must be provided by the operator in a local private env file. The repository should only contain examples, never live secrets.

## Trading safety

This module is designed around explicit user confirmation. Monitoring is safe to automate, but placing, replacing, and cancelling orders should remain confirmation-gated unless the operator intentionally changes that rule.

## Cleanup before publication

Before publishing:
- remove exported local packages that contain personal handoff notes;
- remove temporary test artifacts;
- ensure docs do not expose secret values;
- ensure examples use placeholders only.
