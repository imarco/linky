# linky

批量链接研究分析工具 —— Claude Code / Codex Skill。

给一批 URL 或本地文本资料，自动归一化 source、提取正文、判断类型、按不同模板生成结构化分析报告。

## 授权边界

Linky 是用户授权的阅读与研究自动化工具。它只处理公开内容，或用户本人已经能在自己的浏览器中正常看到的内容。
浏览器能力用于减少打开页面、读取可见正文、整理笔记和归档报告等重复操作。

如果页面对用户不可见，或需要额外授权、付费、验证码、加入组织、切换账号等人工确认，Linky 会把链接标记为受限或 pending，
不会尝试获取用户无权查看的内容。

GPT/Codex 之间的安全调用边界见 [`references/gpt-safe-contract.md`](references/gpt-safe-contract.md)。

## 功能

- **正文提取**：Jina Reader → Trafilatura → Scrapling + html2text → WebFetch → 浏览器自动化，多级降级策略
- **Source intake**：URL 交给现有 extraction pipeline；本地 `.md` / `.txt` 直接纳入；PDF/Office 通过可选 `markitdown` 转换
- **类型识别**：自动分类为 Git 仓库 / 产品官网 / 文章 / 视频 / 社媒帖文 / 文档 / 平台等
- **差异化分析**：不同类型使用不同分析卡模板（项目分析卡、产品研究卡、内容洞察卡等）
- **多视角判断**：综合技术、产品、投资、内容创作视角给出独立判断和后续行动建议
- **多种输出**：Notion / 单文件 Markdown / 多文件 Markdown / Prompt 模式（喂给其他 AI 平台）
- **配置进化**：偏好和模板累积在 `~/.config/linky/`，越用越贴合个人需求

## 安装

### Claude Code / Codex

```bash
npx skills add -y -g https://github.com/imarco/linky
```

## 使用

在 Claude Code 中直接说：

```
帮我研究这些链接：
https://github.com/anthropics/claude-code
https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview
https://simonwillison.net/2025/Jan/24/claude-code/
```

或者：

```
看看这些链接，输出成 prompt 模式，我要喂给 deepseek 做进一步整理：
https://github.com/langgenius/dify
https://dify.ai/
```

## 采集策略

仓库内置了默认的网页采集策略（`references/fetch-strategy.toml`），包含：

- **降级链**：Jina Reader → Trafilatura → Scrapling + html2text → WebFetch → 浏览器自动化
- **域名快捷路由**：微信公众号直接走 Scrapling（跳过 Jina），小红书走浏览器自动化等
- **正文选择器**：通用选择器 + 特定域名选择器覆盖
- **html2text 参数**：保留链接、图片，不自动折行
- **质量门禁与 trace**：低质量正文继续 fallback；本地 trace 默认写入 `.linky/runs/`
- **研究循环与轻量图谱**：支持 autoresearch loop 和 JSON ResearchGraph 中间数据

首次使用时会自动拷贝到 `~/.config/linky/fetch-strategy.toml`。
你可以修改本地副本来自定义覆盖（比如添加新的域名路由、调整降级顺序），仓库更新不会覆盖你的自定义配置。

## 架构

Linky 仍然是本地优先的 Skill 工具，不是线上服务。当前架构分为：

1. **输入归一化**：解析 URL、去重、识别用户预提取正文。
2. **Source intake**：把 URL、本地 Markdown/text、可转换文档归一化为 `SourceArtifact`，并记录 intake trace。
3. **域名计划**：按域名分 batch，加载 domain metadata、授权上下文和 domain route。
4. **Extraction**：按 `fetch-strategy.toml` 的 provider fallback 执行，输出 `ExtractionResult` 和 `ExtractionTrace`。
5. **Classification**：基于 URL、metadata、正文和域名知识判断主类型。
6. **Autoresearch loop**：执行 `plan → extract/analyze → critique → gap detection → optional补采 → final synthesis`，用于发现缺口和补采。
7. **ResearchGraph**：用轻量 JSON 图记录 `url/document/entity/topic/claim/action` 节点和 typed edges，不引入图数据库或向量库。
8. **ReportData → Markdown**：先形成结构化中间数据，再渲染 Markdown、Notion、Obsidian 或 Prompt 模式。

Firecrawl、Crawl4AI、GraphRAG、GPT Researcher、Anything-to-NotebookLM 等项目会放在本地 `refs/` 目录中作为架构参考。Firecrawl 不作为默认 runtime dependency；只有未来显式配置 provider 时才会调用外部服务。

腾讯 ima、NotebookLM、Feishu 记录为未来 output target 候选，见 [`references/output-targets.md`](references/output-targets.md)。它们不会作为当前默认 runtime dependency。

## 示例输出

`references/examples/` 下有两份真实运行产出，可作为报告结构和质量的参考标杆：

- [`report-openclaw-agent-ecosystem.md`](references/examples/report-openclaw-agent-ecosystem.md) — 17 条链接的 Agent 生态研究，多类型混合
- [`report-misc-mixed-batch.md`](references/examples/report-misc-mixed-batch.md) — 5 条分散主题的小批量研究

## Benchmark

`evals/` 下包含 3 条评估用例，覆盖 skill 的核心使用场景。最近一次对照实验结果：

| 配置 | 平均通过率 | 平均 tokens | 平均耗时 |
|------|-----------|------------|----------|
| **with_skill**     | **94.4%** (20/21) | 57,338 | 287.7s |
| without_skill 裸跑 | 39.5% (8/21)      | 36,926 | 231.9s |

通过率 **+55 个百分点**，token 开销约 +55%，耗时 +24%。skill 带来的核心增益是结构化的
A/B/C 报告大纲、类型分组、分析卡模板差异化，以及「我的判断 + 建议后续行动」这两个
baseline 完全没有的字段。详见 [`evals/README.md`](evals/README.md)。

## 配置

首次使用时自动初始化 `~/.config/linky/`：

```
~/.config/linky/
├── config.toml            # 全局设置（默认输出方式、批量大小等）
├── fetch-strategy.toml    # 采集策略（覆盖仓库默认值）
├── personas/              # 分析视角定义
├── templates/             # 自定义分析卡模板（覆盖默认）
├── good-shots/            # 优质输出示例（质量标杆）
└── memory.md              # 累积偏好、规则、账号和全局记忆
```

## License

MIT
