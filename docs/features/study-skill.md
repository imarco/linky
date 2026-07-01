# Feature: study-skill

## Problem

用户在进行深度学习（阅读技术文档、PDF、论文、长文）时，需要把原始内容转化为可检索、可复习、可交互的结构化学习材料。现有工具各有不足：

- **linky**：专注于批量链接的「研究分析」—— 产出研究报告、分类摘要、竞品调研，面向决策支持，但不专注于学习场景（笔记结构化、知识卡片、交互式复习、认知地图）
- **knowledge-absorber (StudyAnalysis-Skills)**：专注于「知识吸收」—— 产出 Markdown 深度笔记 + 交互式 HTML 知识卡片，支持 Mermaid 认知地图、Mentor Mode、真理锚定协议，但不擅长多链接批量处理、域名路由、输出适配

用户需要在 linky 中新增**学习模式（study mode）**，融合两者优势：linky 的批量处理和内容提取基础设施 + knowledge-absorber 的知识卡片、认知地图和交互式学习设计。

**设计决策（office-hours Phase 3-4）：** 选择在 linky 内部扩展 `--mode=study`，而非创建独立 skill。理由：一个工具、一个触发点、全部基础设施复用。

## Goals

1. **学习优先的产出**：产出面向学习的结构化材料（深度笔记、知识卡片、认知地图），而非面向决策的研究报告
2. **多源并发处理**：支持批量 URL/PDF/文档同时处理（借用 linky 的提取能力）
3. **知识卡片 (Knowledge Cards)**：生成结构化 Markdown 笔记 + 交互式 HTML 知识卡片，支持搜索、Mermaid 图、代码高亮
4. **认知地图 (Cognitive Maps)**：自动提取概念关系，生成 Mermaid 思维导图
5. **真理锚定 (Truth Anchoring)**：关键知识点经过网络验证，标记 [已过时] / [存在争议] / [待确认]
6. **类型自适应**：根据内容类型（技术文档、教程、论文、博客）采用不同的分析框架和输出风格
7. **本地优先**：所有处理在本地完成，不依赖外部服务（Mentor Mode 为可选增强）

## Non-goals

- 不复制 linky 的研究报告/竞品调研输出格式（那是 linky 的领地）
- 不实现完整的 Mentor Mode 交互式 AI 教学（可作为后续增强，v1 不含）
- 不做 Obsidian/Notion 输出适配（linky 已有这些适配器，可复用但非 v1 范围）
- 不做本地配置文件系统（`~/.config/study-skill/`）—— v1 使用 skill 内置默认值
- 不做完整的 RAG/向量检索（超出 skill 范围）

## Scope and Boundaries

**Included (v1):**
- 作为 linky 的 `--mode=study` 输出模式扩展
- 输入：复用 linky 的 URL/PDF/文档输入机制
- 处理：linky 内容提取 + scrapling_fetch.py 动态页面处理 → study 模式分析流水线
- 输出：`<name>.md`（深度笔记）+ `<name>.interactive.html`（交互式知识卡片）
- 卡片功能：搜索过滤、Mermaid 认知地图、代码高亮、暗/亮模式切换
- 真理锚定：通过 web search 验证关键断言
- 多源交叉分析：当输入多个链接时，识别共同概念、冲突观点、知识差距

**Excluded:**
- 不作为独立 skill（已决定在 linky 内扩展）
- AI 导师对话系统（Mentor Mode —— 后续版本）
- 在线服务/API 部署
- 输出到第三方平台（Obsidian、Notion 等 —— linky 已有适配器，后续可复用）

**User roles:** 技术学习者（主要）、研究人员、内容创作者

## UX / API Contract

### 触发方式
复用 linky 的触发机制，当用户表达"学习"、"深度阅读"、"做笔记"、"知识卡片"、"学习材料"等意图时，linky 识别为 study 模式并路由到学习分析流水线。

### 输入（linky 扩展）
```
linky <url1> <url2> ... --mode=study        # 一个或多个 URL
linky <path1> <path2> ... --mode=study      # 一个或多个本地文件路径
linky <url> --mode=study --style=<mode>     # 指定输出风格
```

### 输出
```
outputs/study-<timestamp>/
├── <source-name>.md               # 深度笔记（Markdown）
├── <source-name>.interactive.html # 交互式知识卡片
├── cognitive-map.md               # 概念关系图（Mermaid 格式）
└── cross-analysis.md              # 多源交叉分析（仅多输入时）
```

### 交互式 HTML 卡片功能
- 🔍 搜索过滤（精确隐藏不匹配内容块）
- 🧠 Mermaid 认知地图（自动修正语法）
- 🌓 暗/亮模式切换
- 📋 代码高亮
- 📑 侧边栏目录导航

## Open Questions

- None

## Design Decision Log

| Date | Decision | Alternatives | Rationale |
|---|---|---|---|
| 2026-06-19 | linky 扩展模式（`--mode=study`）| A: 独立 skill + linky 脚本; B: 完全独立实现 | 一个工具、一个触发点、全部基础设施复用 |
| 2026-06-19 | 内容提取使用 linky Python 脚本 | 仅 Claude 原生工具 | scrapling_fetch.py 提供 JS 渲染和动态页面处理能力 |
| 2026-06-19 | v1 不含 Mentor Mode | 完整实现 Mentor Mode | 降低复杂度，v1 聚焦核心知识卡片 |
| 2026-06-19 | HTML 卡片完全离线 | 允许 CDN | 学习材料需要任何环境可用 |
