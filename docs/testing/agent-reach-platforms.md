# Testing Matrix: Agent Reach Platform Approaches for Linky

## Source

- Feature spec: ../features/agent-reach-platforms.md
- Standard test cases: ../test-cases/agent-reach-platforms.md

## Coverage Matrix

| Requirement | Test Case | Automated? | Command / Evidence |
|---|---|---|---|
| Strategy can define platform providers | Strategy loads platform providers | yes | `python3 -m unittest tests.test_strategy_and_extraction` |
| Domain planner prefers native platform routes | Platform route jumps to native provider | yes | Add URL route fixtures in strategy/domain tests |
| Missing dependencies do not crash extraction | Missing CLI is skipped with trace | yes | Add command-checker injection tests |
| Install surface identifies CLI/module gaps | Install check reports auto-installable dependencies | yes | Add focused install/doctor unit tests |
| Doctor reports provider readiness | Doctor reports provider readiness | yes | Extend `tests.test_source_intake_and_doctor` |
| Platform parsers normalize CLI/API output | YouTube/GitHub/V2EX/XHS parser cases | yes | Add JSON/text fixtures under `tests/fixtures/` |
| Login-required providers fail closed | Login-required providers fail closed | yes | Fixtures with unauthenticated command/API output |
| Existing generic extraction still works | Regression tests | yes | Existing unittest suite |

## P0 Blockers

- None

## Release Gates

- `python3 -m unittest tests.test_strategy_and_extraction`
- `python3 -m unittest tests.test_platform_providers`
- `python3 -m unittest tests.test_source_intake_and_doctor`
- `python3 -m unittest tests.test_graph_and_report`
- `python3 -m unittest tests.test_gpt_safe_surface`
- `python3 -m unittest tests.test_study_mode`
- Manual smoke, only when corresponding tools are installed: `bin/linky-doctor`
  shows platform provider readiness without exposing secrets.

## Risk Checks

- Verify no implementation shells out to `agent-reach`.
- Verify no upstream repo is cloned into the Linky workspace.
- Verify `bin/install` does not use sudo automatically.
- Verify traces redact saved sessions, tokens, and browser state.
- Verify docs describe Agent Reach as a research source, not a runtime
  dependency.
