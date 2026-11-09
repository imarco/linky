# Controlled resource acquisition implementation plan

> Execute test-first and obtain an independent whole-branch review before publication.

**Goal:** Extend Linky with bounded public resource acquisition while retaining research and study.
**Architecture:** Isolated safe HTTP transport, acquisition/result layer, CLI and skill routing; existing intake consumes only completed files on explicit user request.
**Tech stack:** Python 3.11+ standard library and existing optional dependencies.
**Spec:** ../specs/2026-11-09-resource-acquisition-design.md

## Constraints and review focus

No credential discovery, authenticated retry, private IPs, unsafe redirects, path traversal, arbitrary execution or archive expansion. Test DNS rebinding, encoded/malformed URLs, deceptive HTML downloads, interrupted/oversize bodies, duplicate paths and partial batches.

## Tasks

- [x] QA PR #6 at c4314bf; fix GH_HOST, V2EX reply attribution, yt-dlp extras/runtime/solver checks, issue/PR test coverage.
- [x] Add failing tests for network validation and pinned transport, then implement scripts/linky/safe_http.py.
- [x] Add failing tests for acquisition, manifest, file safety, GitHub paths, media opt-in and article discovery, then implement scripts/linky/acquire.py and bin/linky-get.
- [x] Document mode routing, user intent boundaries, supported formats and limitations. Retain upstream MIT notice.
- [ ] Run all existing and new tests, compile/help checks and permitted live public scenarios; distinguish actual network limits from product failures.
- [ ] Independent review, fix findings, rerun full regression, publish branch, verify remote commit and CI, merge only after checks.
- [ ] Validate fixed skill through supported installation path; stop if scanning rejects it.
