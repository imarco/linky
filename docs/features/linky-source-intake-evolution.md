# Linky Source Intake Evolution

## Goal

把 Linky 的入口从 URL 批量研究扩展为多源输入归一化底座。第一期只实现本地 source intake、intake trace、optional dependency 检查和 doctor，不实现 NotebookLM、腾讯 ima、Feishu 或付费墙访问研究 provider。

## Current State

- 现有 pipeline 从 URL extraction 开始，核心 contract 是 `ExtractionResult` 和 `ExtractionTrace`。
- `references/fetch-strategy.toml` 已经描述 extraction provider、domain route、quality threshold、trace 和 graph 开关。
- 输出侧已有 filesystem、Obsidian、Notion、Yinxiang 等 adapter surface，但 NotebookLM、腾讯 ima、Feishu 只作为未来候选。
- `joeseesun/qiaomu-anything-to-notebooklm` 已作为本地 reference checkout 放入 ignored `refs/`，研究摘要在 `references/qiaomu-anything-to-notebooklm-study.md`。

## Scope

### In Scope

- 新增 source intake 层，支持 URL、`.md`、`.txt`、PDF/Office 文件。
- URL 输入只归一化，不在 intake 层抓取正文，继续交给现有 `extract_url` fallback chain。
- `.md` / `.txt` 本地文件直接读入 `SourceArtifact`。
- PDF/Office 文件通过 optional `markitdown` 转换；缺失依赖时返回 `missing_dependency`，不让 batch 崩溃。
- 定义 `SourceInput`、`SourceArtifact`、`SourceKind`、`IntakeTrace`，并提供 `intake_source` / `intake_sources` 调用入口。
- 新增 doctor 能力和 `bin/linky-doctor` CLI，报告 extraction providers、optional Python modules、外部 CLI/commands 的 ready/missing/disabled 状态。
- 更新 docs/test/testing matrix，明确 future output targets 和 future paywall access research track。

### Out of Scope

- 不实现 NotebookLM、腾讯 ima、Feishu 的发布或上传逻辑。
- 不实现付费墙访问研究 provider，不新增 disabled scaffold。
- 不改变 legacy `scripts/scrapling_fetch.py <url> [max_chars]` 行为。
- 不引入线上服务、正式 Python package、GraphRAG、向量数据库或图数据库。

## Architecture Direction

Source intake 位于 extraction 之前：

1. Parse input：识别 URL、本地文件、未知文本或不支持类型。
2. Normalize source：生成 `SourceArtifact`，保留原始 locator 和 normalized artifact。
3. Convert if needed：仅 PDF/Office 调用 optional `markitdown`，并记录 trace。
4. Hand off：URL artifact 后续进入 extraction；文本/转换结果可进入 classification、report 或 future output bundle。
5. Doctor：读取 strategy 和环境，报告可用能力，不安装依赖、不联网。

## Public Contracts

### SourceInput

Required fields:

- `raw`
- `metadata`

### SourceArtifact

Required fields:

- `id`
- `kind`
- `original_uri`
- `artifact_path_or_text`
- `status`
- `metadata`
- `quality`
- `trace`
- `errors`

### Intake Functions

Required behavior:

- `intake_source(source)` normalizes one source into one `SourceArtifact`.
- `intake_sources(sources)` normalizes a batch and keeps recoverable failures visible as per-item artifacts.
- URL artifacts do not fetch content; they set `metadata.extraction_pipeline = "existing_url_pipeline"` for downstream extraction.

### SourceKind

Initial values:

- `url`
- `markdown`
- `text`
- `pdf`
- `office`
- `unsupported`

### IntakeTrace

Required fields:

- `input`
- `steps`
- `final_status`
- `started_at`
- `finished_at`

Status values:

- Existing extraction/report statuses remain `success | partial | blocked | failed`.
- Intake adds `unsupported | missing_dependency | restricted | pending_user_action`.

### Doctor Report

Doctor returns structured data with:

- `providers`: configured extraction provider readiness.
- `modules`: Python module readiness such as `markitdown`, `trafilatura`, `scrapling`.
- `commands`: external command readiness such as `playwright-cli`.
- `status`: `ready | missing | disabled`.

## Future Tracks

- Output targets: Tencent ima, NotebookLM, Feishu and prompt bundle should share a future destination contract, but are not implemented now.
- Paywall access research: keep as a future track with its own authorization model, domain policy table, trace semantics and review gate before implementation.

## Resolved Defaults

- `markitdown` is optional. Missing dependency returns a structured artifact with `missing_dependency`.
- Local files are read as UTF-8 with replacement behavior for invalid bytes.
- Doctor is read-only and never installs dependencies.
- The qiaomu reference source remains ignored under `refs/`.
