# Bin Script Layout Drift Note

Date: 2026-06-23

## Change

- Move user/developer operation entrypoints to `bin/`.
- Keep Linky runtime modules, adapters, and crawler wrappers under `scripts/`.

## Canonical Docs To Sync

- `SKILL.md`: config initialization path now uses `bin/init-config.sh`.
- `docs/features/linky-source-intake-evolution.md`: doctor CLI path now uses `bin/linky-doctor`.
- `docs/test-cases/linky-source-intake-evolution.md`: doctor CLI compatibility case now uses `bin/linky-doctor --help`.

## Runtime Boundary

- `scripts/linky/`, `scripts/adapters/`, and `scripts/scrapling_fetch.py` remain runtime files.
- `bin/init-config.sh` and `bin/linky-doctor` are operation entrypoints.
