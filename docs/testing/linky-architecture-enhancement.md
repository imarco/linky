# Testing Matrix: Linky Architecture Enhancement

## Coverage Matrix

| Area | Unit | Fixture | Integration | Status |
|---|---:|---:|---:|---|
| Strategy loader | Required | Required | Required | planned |
| Provider fallback | Required | Required | Required | planned |
| Quality scoring | Required | Required | Optional | planned |
| Legacy CLI wrapper | Required | Required | Required | planned |
| Extraction trace | Required | Optional | Required | planned |
| Research graph | Required | Optional | Optional | planned |
| ReportData rendering | Required | Required | Required | covered: standard, 极简白话, explanatory, and learning unit tests |
| Output adapters | Existing smoke | Optional | Optional | planned |

## P0 Release Gates

- `scripts/scrapling_fetch.py <url> [max_chars]` remains compatible.
- Existing eval expectations still map to A/B/C report structure.
- Strategy loading is covered by automated tests.
- Provider fallback writes trace for success and failure paths.
- Optional dependencies fail closed: missing dependency must not crash the whole batch.
- No remote service dependency is required by default.
- `refs/` is ignored by git.

## P1 Gates

- Local fixture tests cover article, GitHub-like README, login wall, and domain selector pages.
- Research graph supports stable node ids and edge type validation.
- README documents the local architecture and non-goals.

## Known Risks

- Overbuilding the Python module could accidentally turn the project into a package before that is wanted.
- Adding too many providers at once can make fallback behavior difficult to reason about.
- Full GraphRAG would add premature dependency and runtime complexity; first phase should remain JSON/file based.
- Existing user edits in `SKILL.md` and `fetch-strategy.toml` must be preserved.
