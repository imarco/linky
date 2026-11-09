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

## Reconciliation with main (2026-11-09)

- Main already provides `bin/linky-doctor` as a wrapper around the shared CLI implementation. Keep that implementation and `scripts/linky_doctor.py` compatibility rather than duplicating it.
- Move config initialization to `bin/init-config.sh`, retaining `scripts/init-config.sh` as a compatibility wrapper.
- Both config entrypoints are tested from an unrelated working directory and preserve user configuration on repeated runs. Existing doctor tests continue covering both entrypoints.
