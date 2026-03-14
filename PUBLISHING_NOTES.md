# Publishing Notes

## What is included intentionally

This public package includes:
- operational docs;
- public-safe scripts;
- auth and trading flow logic without live secrets;
- examples and quick-start notes.

## What must be checked before push

- no live secrets in scripts or docs;
- no local-only export packages;
- no personal backup references;
- no hidden env files copied into the repo;
- no test artifacts left in examples or scripts.

## Recommended publication flow

1. Run a secret scan.
2. Review all copied files manually.
3. Initialize local git repository.
4. Commit sanitized package.
5. Push only after final human review.
