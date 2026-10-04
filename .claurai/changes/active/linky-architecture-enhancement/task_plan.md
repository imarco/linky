# Task Plan: linky-architecture-enhancement

## Meta

- Subproject: linky-architecture-enhancement
- Created: 2026-05-09
- Owner: marco
- Base branch: main
- Feature branch: main

## Goal

Build a local-first Linky architecture foundation that preserves the current Skill workflow while adding extraction contracts, strategy-driven fallback, traceability, lightweight research graph support, and an autoresearch loop.

## Architecture Summary

The implementation should keep Linky as a Skill-first local tool. The new architecture introduces an internal Python pipeline under `scripts/linky/`, where TOML strategy files drive provider selection and fallback. Each URL extraction produces structured results and trace data. Research synthesis remains Markdown-first externally, but internally flows through structured `ReportData`, with optional lightweight graph data available for synthesis and future GraphRAG work.

## Current Phase

Review

## Phases

### Phase 0: Planning Baseline And Reference Repos

- **Status:** complete
- **Verification command:** `git status --short && test -d docs/features && test -d .claurai/planning/linky-architecture-enhancement`
- **Discipline:** docs-first
- **Files:**
  - `.gitignore`
  - `docs/features/linky-architecture-enhancement.md`
  - `docs/test-cases/linky-architecture-enhancement.md`
  - `docs/testing/linky-architecture-enhancement.md`
  - `docs/plans/roadmap.md`
  - `docs/plans/current-status.md`
- **Tasks:**
  - [x] Create `refs/` during execution and shallow clone the selected reference repositories.
  - [x] Confirm `refs/` remains ignored by git.
  - [x] Preserve existing user edits in `SKILL.md` and `references/fetch-strategy.toml`.

### Phase 1: Skill Flow And Strategy Documentation

- **Status:** complete
- **Verification command:** `rg "autoresearch|ResearchGraph|ExtractionResult|Firecrawl" SKILL.md README.md references`
- **Discipline:** docs + compatibility
- **Files:**
  - `SKILL.md`
  - `README.md`
  - `references/fetch-strategy.toml`
  - `references/output-formats.md`
- **Tasks:**
  - [x] Rewrite the Skill flow around input normalization, domain plan, extraction, classification, autoresearch loop, lightweight graph, report assembly, and output adapter.
  - [x] Document Firecrawl as reference-only unless explicitly configured later.
  - [x] Add config fields for providers, fallback order, quality threshold, research loop, and graph output.
  - [x] Keep existing Playwright CLI changes intact.

### Phase 2: Internal Extraction Contracts

- **Status:** complete
- **Verification command:** `python3 -m unittest discover -s tests -v`
- **Discipline:** light refactor
- **Files:**
  - `scripts/linky/`
  - `scripts/scrapling_fetch.py`
  - `references/fetch-strategy.toml`
  - `tests/`
- **Tasks:**
  - [x] Add internal dataclasses/contracts for `ExtractionResult` and `ExtractionTrace`.
  - [x] Add a strategy loader for `fetch-strategy.toml`.
  - [x] Move Scrapling extraction into provider module while preserving the legacy wrapper CLI.
  - [x] Add quality scoring and fallback reasons.

### Phase 3: Research Graph And Report Data

- **Status:** complete
- **Verification command:** `python3 -m unittest discover -s tests -v`
- **Discipline:** data contract
- **Files:**
  - `scripts/linky/`
  - `references/output-formats.md`
  - `tests/`
- **Tasks:**
  - [x] Add `ResearchGraph` with fixed node and edge types.
  - [x] Add graph node/edge de-duplication.
  - [x] Add `ReportData` as the structured source for Markdown rendering.
  - [x] Ensure blocked and partial links remain visible in report data.

### Phase 4: Fixtures, Eval Harness, And Documentation Sync

- **Status:** complete
- **Verification command:** `python3 -m unittest discover -s tests -v && python3 scripts/scrapling_fetch.py --help >/dev/null`
- **Discipline:** verification
- **Files:**
  - `tests/fixtures/`
  - `evals/`
  - `README.md`
  - `docs/`
- **Tasks:**
  - [x] Add fixture pages for article, GitHub-like README, login wall, and selector-specific pages.
  - [x] Add tests for TOML loading, fallback, trace serialization, graph de-duplication, and legacy CLI compatibility.
  - [x] Update README with architecture, local running, refs, and non-goals.
  - [x] Sync accepted behavior back into canonical docs before closing the phase.

## Errors Encountered

| Error | Attempt | Resolution |
|---|---|---|
| Canonical `plugins/claurai-flow-claude/commands/plan.md` missing in repo | Read repo-relative path | Located installed canonical file under Codex plugin cache |
| `request_user_input` unavailable in Default mode | Tried to ask cf-plan choices | Used conservative defaults: `linky-architecture-enhancement`, depth `full` |
| Delegate Skill tool not exposed as separate callable runtime handoff | Checked delegate files on disk | Recorded a visible cf-plan note and did not claim delegate reviews ran |
| `pytest` not installed in local Python 3.14 environment | Checked Python test environment before implementation | Wrote tests with standard-library `unittest`; they remain pytest-discoverable later |

## Decisions Log

| Date | Decision | Tier | Rationale |
|---|---|---|---|
| 2026-05-09 | Use docs as fact source before task plan | Product/process | Matches updated cf-plan flow and avoids task_plan becoming source of truth |
| 2026-05-09 | Default subproject name is `linky-architecture-enhancement` | Process | Clear, specific, and aligned with the planned work |
| 2026-05-09 | Do not clone refs during planning step | Execution boundary | Current request is plan optimization, not implementation execution |
| 2026-05-09 | Use unittest as local verification command | Verification | Avoids adding test-runner dependency while preserving pytest-compatible test files |
