# qiaomu-anything-to-notebooklm Study

## Snapshot

- Upstream: `joeseesun/qiaomu-anything-to-notebooklm`
- Local source checkout: `refs/qiaomu-anything-to-notebooklm/`
- Local snapshot: `cea6cee` (`2026-04-28`, `Update skill`)
- Git tracking rule: source checkout is ignored by `.gitignore:6` via `refs/`
- Purpose in Linky: reference only. Do not vendor this source into runtime code.

## What It Is

`qiaomu-anything-to-notebooklm` is a Claude Code Skill style workflow for turning many kinds of source material into NotebookLM outputs. The project is organized around a natural language trigger, a Python CLI (`main.py`), shell/Python helper scripts, and optional MCP servers.

Its stated workflow is:

1. Detect content source type from URL or file path.
2. Fetch or convert the source into text/Markdown when needed.
3. Upload the source to NotebookLM through the `notebooklm` CLI.
4. Optionally ask NotebookLM a fixed progressive question set.
5. Export generated artifacts or structured JSON, with an optional Feishu document path.

## Capabilities Worth Studying

### Multi-source input normalization

`main.py` classifies URLs and files into types such as WeChat, YouTube, podcast, X/Twitter, EPUB, document, office file, image, audio, zip, and search query. Linky currently focuses on URL batches; this reference shows how a broader intake layer could treat local files, media, and web links as one normalized source queue.

Borrow the idea, not the exact implementation. Linky should model this as a `SourceArtifact` or extended `ExtractionResult`, with fields for source kind, original locator, normalized local artifact, conversion provider, metadata, quality, trace, and user-action status.

### Progressive question plan

The deep-analysis flow uses three rounds:

1. Overview and structure.
2. Deep evidence, tensions, and critique.
3. Synthesis, action guidance, and reasons to read.

This is a concrete version of Linky's planned autoresearch loop. Linky can reuse the pattern as configurable question-plan templates per source type and report mode, then store answers in `ReportData` or a future `ResearchSession` object instead of treating NotebookLM as the only analysis engine.

### Future destination adapters

The reference treats NotebookLM as both ingestion target and generation engine, and also includes a Feishu document creation path. Linky already has filesystem, Obsidian, Notion, Yinxiang, and API adapter surfaces. The useful lesson is the adapter boundary, not NotebookLM itself as a near-term target.

Future output targets can be recorded behind explicit destination contracts:

- `tencent_ima`: export normalized source bundles or rendered reports into Tencent ima workflows.
- `notebooklm`: upload sources and optionally run a question plan, deferred until there is a concrete user workflow.
- `feishu`: create or update a document from rendered Markdown.
- `prompt_bundle`: package normalized sources and question plans for manual upload to external AI tools.

NotebookLM should not be part of the current implementation roadmap. Keep it as a future optional integration candidate only.

### Environment doctor

The reference includes `install.sh` and `check_env.py` to verify Python, Playwright, markitdown, NotebookLM CLI, MCP files, and authentication. Linky would benefit from a lighter `scripts/linky_doctor.py` that checks only enabled providers and adapters from `references/fetch-strategy.toml` plus user config.

This should report capability states such as `ready`, `missing_dependency`, `needs_login`, `needs_user_browser`, and `disabled`, rather than trying to install everything eagerly.

### Human-in-the-loop status

The URL fetch script reports an `ARCHIVE_CAPTCHA` condition with a special exit code. The useful pattern is not unrestricted access logic; it is an explicit pending state when a provider needs user action. Linky should represent this in trace data as `pending_user_action`, with a message and retry hint.

## Capabilities To Defer Or Rework

### Paywall access research is worth studying later

The reference advertises broad paywall access tactics via bot user agents, referer spoofing, AMP, archive.today, Google cache, and other methods. This is a valuable future research direction for Linky because it captures a concrete provider cascade, domain-specific tactics, paywall detection, and human-verification handoff.

For the current Linky phase, keep this deferred. Linky's README defines a stricter authorization boundary: public content or content the user can already see in their own browser. Near-term borrowing should be limited to:

- Paywall/login-wall detection.
- Clear `restricted` or `pending_user_action` states.
- Domain-specific route metadata.
- A future `paywall_research` provider family behind explicit config, tests, and user-controlled enablement.

Do not add paywall access research as a default provider now. When this becomes active work, treat it as a separate design/review phase with its own authorization model, source citations, provider trace semantics, and domain policy table.

### Do not copy hardcoded provider logic

The reference keeps domain lists and fallback logic inside `scripts/fetch_url.sh`. Linky already has `references/fetch-strategy.toml`, quality scoring, provider fallback, and trace contracts. Any borrowed source-specific behavior should become configuration plus tested provider code, not another monolithic shell script.

### Treat README claims as unverified until backed by code

Some documented capabilities are broader than the checked-in implementation. Examples from the local snapshot:

- `main.py` detects `search`, but there is no search branch in the main processing flow.
- `requirements.txt` does not list `ebooklib`, while EPUB extraction imports it.
- `install.sh` expects `wexin-read-mcp`, but the local checkout contains `feishu-read-mcp` and clones WeChat MCP dynamically.
- `scripts/fetch_url.sh` exits on archive CAPTCHA before the later Google Cache and `agent-fetch` sections can run.
- `feishu-read-mcp/src/server.py` annotates `Optional` without importing it.

Use this project as a workflow reference, not as a quality baseline.

## Recommended Linky Evolution

### 1. Add a source intake layer

Current Linky extraction starts from URLs. Add a small intake module that converts mixed inputs into normalized source records:

- URL sources: keep current extraction pipeline.
- Local documents: convert via `markitdown` when configured.
- EPUB: add a tested converter provider only if the dependency is present.
- YouTube: preserve URL and optionally route directly to a downstream adapter that supports YouTube.
- Audio/video/podcast: support transcript providers as optional plugins.

Completion criteria:

- Input records are typed before extraction.
- Conversion output is traceable and quality-scored.
- Missing optional dependencies produce clear pending/error states.

### 2. Defer NotebookLM and define the output adapter boundary

Do not implement NotebookLM in the current phase. Instead, keep the core output boundary generic enough that Tencent ima, NotebookLM, Feishu, and prompt-bundle exports can be added later without changing extraction or report contracts.

Minimal contract:

- `prepare_bundle(items, destination) -> AdapterResult`
- `publish_or_export(bundle, destination_config) -> AdapterResult`
- `run_question_plan(question_plan) -> QuestionRun` for destinations that support conversational generation
- `export_result(format) -> AdapterResult`

Keep authentication and CLI availability checks in doctor output. Do not make NotebookLM, Tencent ima, or Feishu required install dependencies.

### 3. Promote question plans into first-class config

Create reference templates for progressive question plans:

- `overview`
- `deep_reading`
- `critique`
- `action_extraction`
- `cross_source_synthesis`

This extends Linky's current report templates without forcing every run into a specific downstream tool. The same plan can drive local LLM prompting, prompt-bundle mode, Tencent ima, or a future NotebookLM adapter.

### 4. Extend trace and statuses

Add status values for integration workflows:

- `converted`
- `uploaded`
- `generated`
- `pending_user_action`
- `restricted`
- `adapter_failed`

This keeps Linky's operational truth visible when a run depends on browser login, external auth, or a third-party generation step.

### 5. Add a doctor command before adding more integrations

Before implementing Tencent ima, NotebookLM, Feishu, or transcript integrations, add a doctor command that reads config and reports:

- enabled extraction providers
- installed Python modules
- available external CLIs
- configured credentials
- browser/profile requirements
- adapter readiness

This avoids a common failure mode in the reference project: broad claims with hidden runtime prerequisites.

## Immediate Backlog

1. Keep the source checkout under ignored `refs/qiaomu-anything-to-notebooklm/`.
2. Add a `source intake` design note before coding local-file/media support.
3. Keep `notebooklm` out of near-term roadmap scope; record `tencent_ima` and `notebooklm` as future output adapter candidates.
4. Add tests around any new status values before implementing adapters.
5. Keep the current paywall boundary unchanged for now, but record paywall access research as a future track that requires separate design and review before implementation.
