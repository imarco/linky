# Testing Matrix: Linky Source Intake Evolution

## Coverage Matrix

| Area | Unit | Fixture | Integration | Status |
|---|---:|---:|---:|---|
| Source kind detection | Required | Required | Optional | complete |
| Markdown/text artifacts | Required | Required | Optional | complete |
| Optional conversion | Required | Required | Optional | complete |
| Batch recoverable failure | Required | Required | Optional | complete |
| Intake trace/status | Required | Required | Optional | complete |
| Doctor report | Required | Optional | Optional | complete |
| Doctor CLI | Required | Optional | Optional | complete |
| Existing extraction compatibility | Required | Required | Required | complete |
| Existing report rendering | Required | Required | Required | complete |

## P0 Release Gates

- URL intake does not fetch content and continues to hand off to existing extraction.
- `.md` and `.txt` files produce successful `SourceArtifact` values.
- Missing `markitdown` produces `missing_dependency` rather than crashing the batch.
- Unsupported extensions produce `unsupported` with trace and errors.
- Doctor is read-only and reports ready/missing/disabled without installing dependencies.
- Existing extraction and report tests continue to pass.
- No live NotebookLM, Tencent ima, Feishu, paywall access, or network service is required.

## P1 Gates

- Fixture tests cover URL, Markdown, text, unsupported file, and optional conversion.
- Doctor tests mock dependency availability and command lookup.
- README and feature docs clearly separate current scope from future output targets and paywall access research.

## Known Risks

- Adding file conversion can blur the boundary between intake and extraction; conversion must stay limited and traceable.
- Optional dependency checks can become noisy if doctor reports every unused provider; report configured providers first.
- Future output targets should not leak into current runtime dependencies.
- Paywall access research must remain a separate design track until explicitly approved.

## Evidence

- `python -m unittest discover tests` could not run in this shell because `python` is not installed.
- `python3 -m unittest discover tests` passed on 2026-05-19: 20 tests, OK.
- `git diff --check` passed on 2026-05-19.
- Safe-surface wording scan passed on 2026-05-19 with no forbidden terms found.
