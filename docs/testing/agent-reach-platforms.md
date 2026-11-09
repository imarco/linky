# Testing Matrix: Agent Reach Platform Approaches for Linky

## Source

- Feature spec: ../features/agent-reach-platforms.md
- Standard test cases: ../test-cases/agent-reach-platforms.md

## Coverage Matrix

| Requirement | Test Case | Automated? | Command / Evidence |
|---|---|---|---|
| Strategy can define platform providers | Strategy loads platform providers | yes | `python3 -m unittest tests.test_strategy_and_extraction` |
| Domain planner prefers native platform routes | Platform route jumps to native provider | yes | `tests/test_strategy_and_extraction.py`, `tests/test_provider_regressions.py` |
| Missing dependencies do not crash extraction | Missing CLI is skipped with trace | partial | Exception trace path covered; live CLI/session failure modes remain unverified |
| Install surface identifies CLI/module gaps and failures | Install status reflects actual results | yes | `tests/test_install.py` with mocked installers, no host changes |
| Doctor reports provider readiness | Doctor reports provider readiness | yes | Extend `tests.test_source_intake_and_doctor` |
| Platform parsers normalize CLI/API output | YouTube/GitHub/V2EX/XHS parser cases | yes | `tests/test_platform_providers.py`, real-shaped JSON3 in `tests/test_provider_regressions.py` |
| Unimplemented providers are identified honestly | Unimplemented providers | yes | `tests/test_provider_regressions.py`; authenticated adapters are not implemented |
| Native providers respect URL, timeout and output limits | Native extraction boundaries | yes | `tests/test_provider_regressions.py` |
| Existing generic extraction still works | Regression tests | yes | Existing unittest suite |

## P0 Blockers

- None

## Release Gates

- Use Python 3.11+ with pytest in the test environment.
- `python3 -m unittest discover -s tests -p 'test_*.py'`
- `python3 -m pytest -q tests` also collects the function-style study/HTML tests
  that unittest discovery does not execute.
- Manual smoke, only when corresponding tools are installed: `bin/linky-doctor`
  shows platform provider readiness without exposing secrets.

Unit tests mock external commands and HTTP; they do not establish live platform
availability. User-installed yt-dlp source/CLI help confirms the
`requested_subtitles` and JSON3 interface. Live YouTube, GitHub auth and session
provider access require separate smoke evidence.

## Risk Checks

- Verify no implementation shells out to `agent-reach`.
- Verify no upstream repo is cloned into the Linky workspace.
- Verify `bin/install` does not use sudo automatically.
- Verify traces redact saved sessions, tokens, and browser state.
- Verify docs describe Agent Reach as a research source, not a runtime
  dependency.
