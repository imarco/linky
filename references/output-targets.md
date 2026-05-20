# Future Output Targets

Linky currently renders local reports and uses existing filesystem, Obsidian, Notion, Yinxiang and prompt-oriented adapter surfaces. This document records future destination targets only; it is not an implementation contract for the current phase.

## Current Boundary

- Source intake and extraction produce normalized artifacts and structured report data.
- Current runtime must not require Tencent ima, NotebookLM, Feishu or any remote publishing service.
- Destination-specific authentication, browser state, upload behavior and generated artifacts are out of scope for the source intake phase.

## Candidate Targets

### Tencent ima

- Intended role: import normalized source bundles or rendered Linky reports into ima workflows.
- Future questions: supported file formats, browser/session requirements, batch limits, update vs create behavior, and whether export should be manual bundle or automated browser flow.

### NotebookLM

- Intended role: optional downstream source upload and question-plan execution when a concrete workflow justifies it.
- Future questions: CLI/API stability, authentication check, notebook lifecycle, source size limits, and whether answers return as structured data.

### Feishu

- Intended role: create or update shared documents from rendered Markdown.
- Future questions: credential handling, image handling, workspace routing, and idempotent update behavior.

### Prompt Bundle

- Intended role: package sources, metadata, trace summaries and question plans for manual use in external AI tools.
- Future questions: bundle format, token budgeting, and whether graph data should be included.

## Minimum Future Adapter Shape

- `prepare_bundle(items, destination)` builds a destination-neutral bundle.
- `publish_or_export(bundle, destination_config)` writes or uploads to a destination.
- `run_question_plan(question_plan)` exists only for destinations with conversational generation.
- Doctor reports readiness, but never installs dependencies.
