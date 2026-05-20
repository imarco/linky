# Linky Architecture Enhancement

## Goal

将 Linky 从“Skill 文档 + 若干脚本”增强为本地运行的链接研究流水线底座。第一阶段保留现有 Skill 使用方式，不做线上服务、不发布正式 Python package，但要让采集、trace、研究循环、轻量 graph 和报告中间数据具备清晰 contract。

## Current State

- Linky 的主要行为定义在 `SKILL.md`，脚本层目前只有配置初始化、Scrapling 抽取和输出适配器。
- `references/fetch-strategy.toml` 已经描述了 fallback chain、domain route 和 selector，但现有抽取脚本尚未真正完整读取这些策略。
- 已有 eval 文档验证报告结构、类型模板、“我的判断”和“建议的后续行动”，但缺少可运行 fixture 和 provider trace 断言。
- 当前工作区已有用户未提交改动：`SKILL.md` 与 `references/fetch-strategy.toml` 中的 Playwright CLI 相关调整，后续实现必须保留并在其基础上增量修改。

## Scope

### In Scope

- 新增 `scripts/linky/` 内部 Python 模块目录，作为本地 pipeline 底座。
- 定义 extraction contract 和 trace contract。
- 保留 `scripts/scrapling_fetch.py <url> [max_chars]` 兼容入口，并将其迁移为 wrapper。
- 让 `references/fetch-strategy.toml` 驱动 provider、fallback、selector、quality threshold、research loop 和 graph 输出开关。
- 新增轻量 research graph 数据结构，支持 URL、document、entity、topic、claim、action 节点。
- 在 research step 引入 autoresearch loop：plan → extract/analyze → critique → gap detection → optional补采 → final synthesis。
- README 和 references 文档同步说明本地架构、运行方式、参考项目和非目标。
- 新建 `./refs/` 作为本地参考项目目录，并加入 `.gitignore`；参考仓库内容不提交。

### Out of Scope

- 不做线上 API 服务。
- 不引入 Firecrawl 作为默认 runtime dependency。
- 不引入完整 GraphRAG、embeddings、向量数据库或图数据库。
- 不发布 pip package。
- 不自动 push。

## Architecture Direction

Linky 第一阶段采用本地、文件驱动、可测试的流水线：

1. Input normalization：解析 URL、去重、识别用户预提取内容。
2. Domain plan：按域名分 batch，加载 domain metadata、授权上下文和 domain route。
3. Extraction：按 provider fallback 执行抽取，输出 `ExtractionResult`。
4. Classification：基于 URL、metadata、正文和 domain knowledge 判断主类型。
5. Autoresearch loop：识别信息缺口，必要时补采相关页面或标记缺口。
6. Lightweight graph：抽取局部研究图，用于综合判断和后续扩展。
7. Report assembly：从结构化中间数据渲染 Markdown A/B/C 报告。
8. Output adapter：继续复用 filesystem、Obsidian、Notion、Yinxiang 等适配器。

## Reference Repositories

第一批本地参考仓库放入 `./refs/`，只用于架构学习：

- `firecrawl/firecrawl`
- `firecrawl/firecrawl-mcp-server`
- `unclecode/crawl4ai`
- `coleam00/mcp-crawl4ai-rag`
- `adbar/trafilatura`
- `vakovalskii/searcharvester`
- `watercrawl/WaterCrawl`
- `assafelovic/gpt-researcher`
- `langchain-ai/open_deep_research`
- `nickscamara/open-deep-research`
- `karpathy/autoresearch`
- `microsoft/graphrag`
- `gusye1234/nano-graphrag`
- `joeseesun/qiaomu-anything-to-notebooklm`

## Public Contracts

### ExtractionResult

Required fields:

- `url`
- `status`: `success | partial | blocked | failed`
- `provider`
- `markdown`
- `metadata`
- `quality`
- `trace`
- `errors`

### ExtractionTrace

Required fields:

- `url`
- `attempts`
- `final_provider`
- `final_status`
- `started_at`
- `finished_at`
- `quality_score`

Each attempt records provider id, status, elapsed milliseconds, error message, content length, and fallback reason.

### ResearchGraph

Node types:

- `url`
- `document`
- `entity`
- `topic`
- `claim`
- `action`

Edge types:

- `mentions`
- `relates_to`
- `supports`
- `cites`
- `follow_up`
- `same_domain`

### ReportData

Report generation should consume structured data first, then render Markdown. This keeps Markdown, Notion, Obsidian and Prompt mode consistent.

## Resolved Defaults

- Add `trafilatura` after `jina` and before `scrapling` in the general fallback chain. Domain routes can still jump directly to `scrapling` or `browser` for dynamic sites or pages that require user-visible browser context.
- Enable trace output by default for local runs and write artifacts under `.linky/runs/{run-id}/`; `.linky/` remains git-ignored.
- First-phase graph output is JSON only. GraphML export is deferred until a concrete visualization workflow needs it.
