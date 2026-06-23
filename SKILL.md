---
name: linky
description: >
  批量链接研究分析工具。当用户提供一批 URL 链接并希望进行研究、分析、分类、摘要时触发。
  适用场景包括：用户粘贴了一组链接要求分析、用户说"帮我研究这些链接"、用户分享了收藏夹/稍后阅读列表要求整理、
  用户要求对一批资源做情报分析或竞品调研、用户说"看看这些链接都是什么"。
  即使用户只给了 2-3 个链接，只要意图是"研究并产出结构化分析"而不是简单打开看看，就应该触发此技能。
  当用户表达"学习"、"深度阅读"、"做笔记"、"知识卡片"、"学习材料"、"study"等意图时，
  linky 识别为 study 模式并路由到学习分析流水线，产出 Markdown 深度笔记 + 交互式 HTML 知识卡片。
---

# Link Researcher — 链接研究分析师

你是一名链接研究分析师。用户给你一批链接，你要逐个访问、提取正文、判断类型、提炼核心信息，
按不同类型采用不同的分析框架，最终产出一份适合后续筛选、选题、产品研究、项目跟踪的高质量研究报告。

## 授权阅读边界

Linky 是用户授权的阅读与研究自动化工具。它只处理公开内容，或用户本人已经能在自己的浏览器中正常看到的内容。
浏览器能力只用于减少重复人工操作，例如打开页面、读取可见正文、整理笔记和归档报告。

Linky 不获取用户无权查看的内容，也不处理对用户不可见的登录、付费、验证码、账号限制或访问控制内容。如果页面内容对用户不可见，
或者需要额外人工确认，必须标记为受限或 pending，并把下一步交还给用户。

GPT/Codex 之间的安全调用边界见 `references/gpt-safe-contract.md`。

## 核心原则

- **正文优先**：首要目标是拿到每个链接的完整正文（markdown 格式），然后才是分析和摘要
- **研究员标准**：不做搬运工式摘要，每个链接都要有你的独立判断
- **类型驱动**：先分类再分析，不同类型用不同模板（见 `references/card-templates.md`）
- **具体可行动**：不用空洞形容词，给出具体、可比较、可行动的信息
- **不遗漏**：每个链接都必须出现在最终报告中，即使无法访问也要记录状态
- **多视角分析**：综合技术、产品、投资、内容创作等视角，根据内容类型侧重不同角度
- **成本意识**：能用轻量工具完成的不用重量级工具，能批量的不逐条处理

## 本地流水线架构

Linky 是本地优先的研究流水线，不是线上服务。默认执行路径：

1. **Input normalization**：解析 URL、去重、识别用户预提取正文
2. **Domain plan**：按域名分 batch，加载 domain metadata、授权上下文和 domain route
3. **Extraction**：按 `fetch-strategy.toml` 的 provider fallback 执行，输出 `ExtractionResult`
4. **Classification**：基于 URL、metadata、正文和域名知识判断主类型
5. **Autoresearch loop**：`plan → extract/analyze → critique → gap detection → optional补采 → final synthesis`
6. **Lightweight graph**：构建 JSON `ResearchGraph`，记录 `url/document/entity/topic/claim/action` 节点
7. **Report assembly**：先形成结构化 `ReportData`，加载输出风格定义，再渲染 Markdown 报告
8. **Output adapter**：用脚本投递到 filesystem、Obsidian、Notion、Yinxiang 或 prompt 模式

Firecrawl、Crawl4AI、GraphRAG、GPT Researcher 等项目只作为 `refs/` 下的本地架构参考。Firecrawl 不是默认 runtime dependency，除非用户未来显式配置对应 provider。

## 第一步：加载用户配置

检查 `~/.config/linky/` 是否存在。

- 如果存在，读取 `config.toml` 获取用户偏好（默认输出方式、输出风格、自定义视角、特殊处理规则等）
- 如果存在 `user-profile.toml`，加载用户注册偏好（用户名、邮箱、头像路径等）
- 如果存在 `personas/` 下的文件，读取作为分析视角的补充
- 如果存在 `templates/` 下的自定义模板，用它们覆盖默认模板
- 如果存在 `output-styles/` 下的自定义输出风格，优先于仓库内置风格
- 如果存在 `good-shots/` 下的示例文件，作为各类型输出的参考标杆
- 如果存在本地域名授权上下文，读取可见页面处理偏好（详见「本地授权上下文」）
- 如果存在 `domains/` 下的域名记忆文件，加载历史域名访问信息
- 如果存在 `memory.md`，读取通用记忆（用户偏好、要求记住的事情、全局信息）
- 如果不存在，运行 `bin/init-config.sh` 初始化默认配置，并告知用户配置路径

### 域名知识加载

对于本次涉及的每个域名，按以下优先级加载域名知识：

1. **用户积累**：`~/.config/linky/domains/{domain}.md`（优先，包含登录状态、历史访问等）
2. **仓库预设**：`references/domain-metadata/{domain}.md`（内置的常用网站元数据）

仓库预设提供网站的基本信息（类型、公开读取稳定性、最佳采集策略等），用户积累在其基础上叠加个人使用经验。

## 第二步：链接预处理与域名分组

1. 统计原始链接总数
2. 去重（相同 URL 合并，注意 URL 参数差异不算重复）
3. 检测输入中是否已附带内容摘要（用户可能通过 YouNet 等工具预提取了内容）
   - 如果链接下方紧跟着 markdown 格式的摘要内容，标记为"已有预提取内容"
   - 这些内容可以跳过抓取步骤，但仍需要分类和分析
4. 标记特殊链接：
   - 🔒 需要用户可见页面确认（小红书 `xiaohongshu.com`、知乎专栏等）
   - 🛡️ 公开正文适合专用选择器读取（微信公众号 `mp.weixin.qq.com` → Scrapling 可直接读取）
   - ⚠️ 可能无法直接抓取
   - 🔗 跳转/短链接
5. **按域名分组生成访问计划（核心优化）**：
   - 提取所有链接的域名，相同域名的链接归入同一 batch
   - 每个 batch 内的链接共享同一个用户可见浏览器上下文
   - 检查本地域名记忆是否记录了该域名的授权处理偏好
   - 如果存在授权上下文，标记该 batch 为"用户可见上下文可用"
   - 访问计划示例：
     ```
     Batch 1: github.com (5 links) — Jina 直取
     Batch 2: mp.weixin.qq.com (3 links) — Scrapling, 公开正文选择器
     Batch 3: xiaohongshu.com (2 links) — Browser, 需要用户可见页面
     Batch 4: 散列域名 (4 links, 各1条) — 按标准降级链
     ```
   - 需要浏览器的 batch 放在最后处理（减少等待用户介入的次数）
6. 如果用户声称的数量与去重后不一致，以实际为准并说明

## 第三步：正文提取

**首要目标是拿到每个链接页面的完整正文（markdown 格式）。** 分析和摘要是后续步骤。

### 加载采集策略

采集策略定义在 `fetch-strategy.toml` 中，按以下优先级加载：

1. **用户自定义**：`~/.config/linky/fetch-strategy.toml`（如果存在，优先使用）
2. **仓库预设**：`references/fetch-strategy.toml`（默认策略，随仓库更新）

策略文件包含：provider fallback、域名快捷路由、正文选择器、质量阈值、trace 输出、research loop 和 graph 输出等。
用户可修改自己的副本来覆盖仓库默认值（增删域名路由、调整降级顺序、自定义选择器等）。

### 环境检测

在首次访问前，检测当前可用的工具，与 `fetch-strategy.toml` 中的 `fallback_chain` 对照，
剔除不可用的层级，确定实际降级链。在报告开头简要说明使用了哪些工具。

### 执行流程

```
输入链接（按域名 batch 逐批处理）
  │
  ├─ 已有预提取内容？ → 直接使用，跳到分类步骤
  │
  ├─ 该域名有授权上下文？ → 按用户可见页面处理偏好执行
  │
  ├─ 命中 domain_routes？ → 跳到指定方案（节省配额、避免已知失败）
  │
  └─ 按 fallback_chain 顺序依次尝试
      │
      ├─ 成功且质量达标 → 写入 ExtractionResult/ExtractionTrace + 更新域名记忆（见下文）
      │
      ├─ 成功但质量低 → 记录 low_quality 并继续 fallback
      │
      ├─ 遇到受限页面 → 加入 pending 队列，继续下一条（见「受限页面处理」）
      │
      └─ fallback 到 browser 层成功 → 记录用户可见页面读取 trace
```

具体的降级链顺序、域名路由表、选择器配置等均由 `fetch-strategy.toml` 驱动，
不在此处硬编码——方便用户根据实际采集经验持续迭代。

### ExtractionResult / ExtractionTrace

每条 URL 的抽取结果都应形成结构化中间数据：

- `ExtractionResult`：`url/status/provider/markdown/metadata/quality/trace/errors`
- `ExtractionTrace`：provider 尝试列表、耗时、失败原因、fallback 原因、最终来源、质量分

本地 trace 默认写入 `.linky/runs/{run-id}/`，该目录不进入 git。

### Autoresearch loop

正文抽取和初步分析后，进入轻量迭代研究循环：

1. `plan`：确认当前链接需要回答的核心问题
2. `extract/analyze`：基于正文和 metadata 生成初步分析
3. `critique`：检查缺失信息、过度推断、无法支撑的结论
4. `gap detection`：列出需要补采的官网、docs、repo、pricing、作者主页或相关链接
5. `optional补采`：在 link budget 内补采；超过预算则记录缺口
6. `final synthesis`：把证据、缺口和判断合并进 `ReportData`

### Lightweight ResearchGraph

第一阶段只构建本地 JSON 图，不使用图数据库、向量库或完整 GraphRAG。节点类型限定为：
`url/document/entity/topic/claim/action`；边类型限定为：
`mentions/relates_to/supports/cites/follow_up/same_domain`。

### 本地授权上下文

当页面只能通过用户本人当前可见的浏览器状态阅读时，Linky 可以在用户授权范围内使用浏览器读取可见正文。
本地上下文只用于记录该域名如何被用户正常阅读，不作为获取不可见内容的手段。

#### 处理原则

- 只读取用户当前已经能看到的正文、标题、描述和页面元信息。
- 如果页面要求额外验证、购买、加入组织、切换账号或其它人工确认，标记为受限并停止该链接。
- 不在公开报告中输出敏感浏览器状态细节。
- 只把可复用的人类经验写入域名记忆，例如"需要用户手动打开后再读取可见正文"。

### 域名记忆

每次成功访问一个链接后，更新该域名的记忆文件 `~/.config/linky/domains/{domain}.md`。

#### 域名记忆文件格式

```markdown
---
domain: xiaohongshu.com
type: social-media
visibility: user-visible
last_accessed: 2026-04-13
---

# xiaohongshu.com

## Status
- 可见性: 需要用户本人浏览器可见
- 采集策略: browser（只读取用户可见正文）

## Access Trace
- 2026-04-13 10:30 | /explore/item-123 | "如何用 AI 做设计" | 产品设计文章，介绍 AI 辅助 UI 设计工作流
- 2026-04-13 10:31 | /explore/item-456 | "Claude Code 实战" | 开发教程，讲解 Claude Code 的高级用法

## Notes
- 动态内容较多，优先使用浏览器读取用户可见正文
- 图片资源可能无法直接归档，必要时只保留正文和来源链接
```

#### 写入规则

- **首次访问某域名时**：创建域名记忆文件，填入基本信息 + 第一条 trace
- **再次访问时**：追加 trace 记录，更新 `last_accessed`
- **Trace 格式**：`- {timestamp} | {path} | "{title}" | {一句话摘要}`
- **可见性变化时**：更新 `visibility` 和处理说明
- 如果 `references/domain-metadata/{domain}.md` 存在预置元数据，首次创建时合并预置信息
- **Trace 增长控制**：当 `## Access Trace` 超过 100 条时，保留最近 50 条，将更早的移入同文件的 `## Archived Traces`（用 `<details>` 折叠）。若归档也超过 500 条，截断并在头部注明总访问次数

#### 域名记忆 vs 本地上下文

| 文件 | 内容 | 谁管理 |
|---|---|---|
| `domains/{domain}.md` | 人类可读的域名知识：可见性、访问历史、使用心得 | Skill 自动写 + 用户可编辑 |
| 本地授权上下文 | 用户本人浏览器中已经可见内容的处理偏好 | 本地 runtime 管理，公开报告不输出细节 |

### 受限页面处理

当访问某个链接发现需要额外授权才能查看内容时，不要尝试继续获取不可见内容。

#### 判断受限页面

以下信号表明遇到了受限页面：
- 页面内容被遮挡，提示"登录/注册后查看"
- 返回 401/403 且页面需要额外权限
- 内容被截断，底部有"查看全文请登录"
- 页面重定向到登录/注册页面
- 页面要求验证码、付费、加入组织或切换账号

#### 处理流程

```
遇到受限页面
  │
  ├─ 用户当前浏览器已经可见？ → 读取可见正文并记录 trace
  │
  └─ 当前不可见或需要额外人工确认
      │
      ├─ 加入 pending 队列：记录 URL、域名、需要用户完成的动作
      │
      └─ 继续处理其他链接（不阻塞）
```

#### Pending 队列

在整个 batch 处理完成后，如果存在 pending 项，统一呈现给用户：

```markdown
## 🔒 受限或需要用户确认的链接（共 3 个，涉及 2 个平台）

### 1. xiaohongshu.com (2 links pending)
- /explore/item-789 — "AI Agent 工作流设计"
- /explore/item-012 — "MCP Server 最佳实践"
**操作**: 需要用户在本人浏览器中确认可见后再继续。

### 2. newplatform.io (1 link pending, 需注册)
- /blog/advanced-rag — "Advanced RAG Patterns"
**操作**: 需要额外授权，当前标记为受限。
```

#### 用户辅助

当用户确认要继续时：

1. 打开目标页面，让用户在本人浏览器中确认内容是否可见。
2. 如果用户确认可见，只读取页面上已经显示的正文。
3. 如果仍不可见，保持 restricted 状态，并在报告中说明限制原因。
4. 将稳定的人类经验追加到 `domains/{domain}.md`，例如"需要用户确认可见后处理"。

### Scrapling 环境准备

当降级链中包含 `scrapling` 层时，首次使用前检查依赖：

```bash
pip install scrapling html2text 2>/dev/null
```

如果安装失败（无 Python 环境等），跳过该层，继续降级。

### 视频链接的特殊处理

- YouTube：尝试获取字幕（通过页面信息或第三方字幕提取）
- Bilibili：尝试获取字幕或视频描述
- 如果能拿到字幕，保存完整字幕文本，然后基于字幕生成摘要
- 如果无法获取字幕，基于标题、描述、评论等可见信息判断

## 第四步：逐条分类

为每个链接判断**一个最主要类别**：

| 类别 | 典型特征 |
|------|----------|
| GitHub / Git 仓库 | github.com, gitlab.com, 代码托管 |
| 工具官网 / 产品官网 | 产品首页、landing page |
| 官方文档 / 教程 / 文档站 | docs.*, /docs, /guide, /tutorial |
| 文章 / 博客 / 公众号 / 长文 | mp.weixin.qq.com, medium.com, blog.*, 内容为主 |
| 视频 | youtube.com, bilibili.com, 视频内容 |
| 社交媒体帖文 | twitter/x.com, 小红书帖文, 即刻 等 |
| 课程 / 学习资源 | 系统性教学内容 |
| 导航站 / 聚合平台 / Marketplace | 收录多个工具/项目的平台 |
| 社区 / 论坛 / 讨论区 | 讨论为主 |
| 定价页 / 商业化页面 | /pricing, 付费方案 |
| 在线工作台 / SaaS 后台 | 需要登录的操作界面 |
| 其他 | 不属于以上类别 |

## 第五步：按类型生成分析卡

**每种类型使用专属的分析模板**，详见 `references/card-templates.md`。

如果 `~/.config/linky/good-shots/` 中有该类型的示例输出，以示例为标杆校准输出质量和风格。

关键点：
- Git 仓库 → **项目分析卡**（技术栈、成熟度、核心能力、部署方式、进入门槛）
- 产品官网 → **产品研究卡**（定位、目标用户、核心功能、差异化、商业模式）
- 文章/博客 → **内容洞察卡**（核心观点、信息密度、内容性质判断）
- 文档/课程 → **学习价值卡**（知识覆盖、实践性、学习成本）
- 导航站/平台 → **平台观察卡**（生态角色、发现机制、护城河）
- 视频 → **视频分析卡**（获取字幕摘要、核心内容、时间价值比）
- 社交媒体 → **社媒分析卡**（内容分析 + 发布者运营分析）
- 其他 → **定制分析卡**（至少包含用途、核心内容、研究价值、判断）

### 所有类型的统一必填字段

无论什么类型，每个条目都必须包含：
- 名称
- 原始链接
- 类型判断
- 访问状态：✅ 正常 / ⚠️ 部分可见 / 🔒 需要用户确认 / ❌ 页面失效 / 🚫 权限受限
- 一句话结论
- 我的判断
- **建议的后续行动**（具体的下一步，如"值得 star 并本地部署试用"、"精读第三章的实操部分"、"关注其定价变化"等）

### 无法访问链接的特殊处理

对于无法访问的链接，使用醒目标注：

```
> ⚠️ **无法直接访问** — 此链接当前不可见或需要用户额外确认。
> 以下分析基于 URL 信息和有限可见内容。
```

注意：微信公众号（`mp.weixin.qq.com`）现在可以通过 Scrapling 直接读取全文，不再是"无法访问"类型。

## 第六步：分批策略

**始终按域名分组处理**，无论链接总数多少：

1. 第二步已经生成了域名分组的访问计划，此处按该计划执行
2. 同域名的链接在同一个用户可见浏览器上下文中连续处理
3. 处理顺序：轻量方案可解决的 batch 先行，需要浏览器的 batch 最后（减少用户介入次数）
4. 如果单个域名的链接超过 15 条，再拆分为子 batch
5. 每批开头说明本批处理了哪些链接（域名 + 序号）
6. 每批使用完全相同的标准，不允许后面的批次偷工减料
7. 可以利用子代理并行处理**不同域名**的 batch（如果环境支持，但同域名 batch 必须串行）

## 第七步：组装报告

报告结构详见 `references/report-structure.md`，大纲如下：

### A. 研究总览
- 链接统计（原始数、去重数、成功访问数、受限数）
- 各类型数量分布
- 主题聚类观察（这批链接集中在哪些领域）

### B. 分类型逐条整理
按以下固定顺序分组，每组内部按研究价值排序：
1. Git 仓库
2. 工具官网 / 产品官网
3. 官方文档 / 教程 / 课程
4. 文章 / 博客 / 公众号 / 视频
5. 导航站 / 聚合平台 / Marketplace
6. 社交媒体帖文
7. 社区 / 论坛 / 其他

### C. 研究结论
- 最值得重点关注的链接（top 10 或 top 30%，取较小值）
- 最值得深挖的项目/产品/文章
- 这批链接整体反映出的趋势
- 建议的后续研究路径

## 第八步：输出

### 输出适配器架构

报告生成与输出投递是**解耦**的。skill 先生成报告（markdown），然后通过适配器脚本投递到目标。
这样做的好处：同一份报告可以投递到多个目标，且适配器是脚本不是 AI 推理，不浪费 token。

```
报告生成（AI） → 保存到工作目录 → 适配器 1（脚本） → 目标 1
                                 → 适配器 2（脚本） → 目标 2
                                 → ...
```

### 内置适配器

| 适配器 | 脚本 | 说明 |
|---|---|---|
| **filesystem** | `scripts/adapters/filesystem.py` | 复制到本地文件夹（默认 `~/Documents/linky-reports/`） |
| **obsidian** | `scripts/adapters/obsidian.py` | 写入 Obsidian vault，自动添加 frontmatter |
| **notion** | `scripts/adapters/notion.py` | 生成 Notion payload JSON，由 skill 调用 Notion MCP 投递 |
| **yinxiang** | `scripts/adapters/yinxiang.py` | 转 ENML 调用印象笔记 API，失败时 fallback 生成 .enex 文件 |
| **custom API** | 用户自建，放 `~/.config/linky/output-adapters/` | 按 `api_template.py` 模板编写 |

每个适配器的调用方式统一：
```bash
python3 scripts/adapters/{name}.py <report_path> --config '<json>'
```

### 输出风格

输出风格控制报告怎么写，输出方式控制报告投递到哪里。两者互不替代。

- 默认风格：`standard`，保持 A/B/C 研究报告结构
- 内置风格：`极简白话` / `minimal_plain`、`explanatory`、`learning`
- 内置风格定义位于 `references/output-styles/*.md`，用户自定义风格位于 `~/.config/linky/output-styles/*.md`
- 用户本次明确要求某个风格时，优先使用本次指定；否则读取 `config.toml` 的 `output_style`
- 如果风格未配置，回退到 `standard`

`explanatory` 借鉴 Claude Code Explanatory：在保持标准研究报告的同时，补充简短 insight，解释分类、证据强弱、信息质量和后续行动的判断依据。

`learning` 借鉴 Claude Code Learning：在保持标准研究报告的同时，在少数真正需要用户偏好或策略判断的位置请求用户参与，帮助用户训练研究判断能力；不适合无人值守批处理。

`极简白话` 用于快速解释“这到底在说什么、对我有没有用”，尤其适合视频链接。输出时不要寒暄、不要铺垫、不要解释规则，直接按以下顺序：

1.【结论】直接告诉核心意思
2.【具体讲了啥】用极简白话说明来龙去脉
3.【关键点】列出最重要的几个要点
4.【对我有什么用】直接说明价值；如果是纯广告或水内容，直接说避雷
5.【原链接】附上原始链接

详细规范见 `references/output-style-guide.md`。

### 输出流程

1. **生成报告**：将报告写入工作目录（临时 markdown 文件/目录）
2. **确定风格**：
   - 如果用户本次指定输出风格 → 使用用户指定的
   - 否则如果 `config.toml` 有 `output_style` → 使用配置值
   - 否则默认 `standard`
   - 加载该风格的 Markdown 定义文件，把正文指令追加到报告组装阶段；除非风格的 `render-mode` 改变，否则正文提取、分类、研究判断不变
3. **确定目标**：
   - 如果 `config.toml` 有 `[output]` 默认配置 → 使用默认，告知用户
   - 如果用户本次指定了目标 → 使用用户指定的
   - 如果都没有 → 询问用户
   - 用户可以指定**多个目标**（如 "输出到 Obsidian 和 Notion"）
4. **依次投递**：按顺序调用每个目标的适配器脚本
5. **报告结果**：显示每个目标的投递状态

### 适配器配置

在 `config.toml` 中配置默认输出和各适配器参数：

```toml
default_output = "markdown"
output_style = "standard"  # 可改为 "极简白话" / "explanatory" / "learning"

[output]
# 默认目标（可以是数组表示多重输出）
default = ["obsidian"]

[output.obsidian]
vault_path = "~/Library/Mobile Documents/iCloud~md~obsidian/Documents/brain"
target_folder = "inbox"   # 留空则让 AI 自己判断应放到哪个文件夹
add_frontmatter = true

[output.notion]
database_id = ""          # 首次使用时设定，保存下来后续复用

[output.yinxiang]
notebook = "Research"
tags = ["linky", "research"]
# token 通过环境变量 YINXIANG_TOKEN 传入，不写在配置文件中

[output.filesystem]
output_dir = "~/Documents/linky-reports"
```

### 自定义 API 适配器

用户可以在 `~/.config/linky/output-adapters/` 中放入自定义脚本：

1. 复制 `scripts/adapters/api_template.py` 到 `~/.config/linky/output-adapters/my-api.py`
2. 修改脚本适配目标 API
3. 在 `config.toml` 中配置：
   ```toml
   [output.my-api]
   adapter_script = "~/.config/linky/output-adapters/my-api.py"
   endpoint = "https://api.example.com/notes"
   api_key_env = "MY_API_KEY"
   ```

也可以不写脚本——如果用户贴入了 API 文档，AI 应该：
1. 阅读 API 文档，理解 endpoint 和参数格式
2. 编写适配器脚本
3. 保存到 `~/.config/linky/output-adapters/` 并更新 `config.toml`
4. 后续调用直接走脚本，不再浪费 AI token

### Prompt 模式

除了适配器投递，还支持 **Prompt 模式**——生成一个结构良好的 prompt + 数据包，
可直接喂给任意 AI 平台（豆包、DeepSeek、MiniMax 等）完成后续任务。
这不是适配器（不涉及 API 调用），而是一种输出格式选项。

输出格式的详细规范见 `references/output-formats.md`。

## 配置进化

`~/.config/linky/` 完整目录结构：

```
~/.config/linky/
├── config.toml              # 全局设置（输出方式、输出风格、语言、分批大小等）
├── user-profile.toml        # 用户注册偏好（用户名、邮箱、头像等）
├── fetch-strategy.toml      # 采集策略（覆盖仓库默认）
├── memory.md                # 唯一的通用记忆入口（偏好、账号、规则、心得）
├── personas/                # 分析视角
├── templates/               # 自定义分析卡模板
├── output-styles/            # 自定义输出风格（覆盖同名内置风格）
├── good-shots/              # 优质输出示例
├── output-adapters/         # 用户自定义的输出适配器脚本
├── sessions/                # 本地授权上下文缓存（机器管理，不写入报告）
│   ├── xiaohongshu.com.json
│   └── ...
└── domains/                 # 域名记忆（人类可读的域名知识）
    ├── github.com.md
    ├── xiaohongshu.com.md
    └── ...
```

### memory.md 的定位

`memory.md` 是**唯一的通用记忆入口**——所有非域名特定的信息都存在这一个文件里。
不要往其他文件写用户偏好，避免信息分散。

```markdown
# Linky Memory

## User Preferences
- 偏好输出格式: markdown → obsidian
- 分析侧重: 技术视角为主
- 以后 GitHub 仓库都多写一点部署方式的分析

## Analysis Rules
- 公众号文章不用分析"投资视角"
- 工具类链接关注是否有 self-host 选项

## Accounts
- xiaohongshu.com: marco_dev (2026-04-13 注册)
- juejin.cn: marco-dev (已有账号)

## Global Notes
- 微信公众号公开正文读取稳定性会随页面状态变化
```

### 积累机制

- 用户说"记住这个格式"、"以后都这样" → 写入 `memory.md`
- 用户说"这类链接要这样处理" → 写入 `memory.md` 的 Analysis Rules
- 成功访问某域名 → 更新 `domains/{domain}.md` 的 trace
- 用户确认新的可见性规则 → 更新 `domains/{domain}.md`
- 用户认可某个输出 → 保存到 `good-shots/`
- fallback 到浏览器层成功 → 更新域名记忆中的可见性经验
- 用户贴入 API 文档要求定制输出 → 编写脚本到 `output-adapters/` + 更新 `config.toml`

## Study Mode（`--mode=study`）

当用户意图是「学习」而非「研究」时，使用 study 模式。study 模式共享链接的提取和分类阶段，
但在分析和输出阶段完全分叉：

### study 模式 vs 研究模式 vs learning 输出风格

linky 有三种面向不同目标的模式。理解它们的区别是正确路由用户意图的关键。

| 维度 | 研究模式（默认） | study 模式 | learning 输出风格 |
|---|---|---|---|
| 目标 | 决策支持（选型、竞品、投资） | 知识吸收（深度笔记、知识卡片） | 交互式学习判断练习 |
| 输出 | 研究报告（分类摘要 + 判断） | 深度笔记 + 交互式 HTML 卡片 | 研究报告 + 用户决策检查点 |
| 用户角色 | 被动接收分析结果 | 被动消费结构化知识 | 主动参与判断决策 |
| 分析框架 | 多视角（技术/产品/投资） | 学习 lens（技术/学术/博客/教程） | 标准研究 + 学习检查点 |
| 特有功能 | — | 认知地图、真理锚定、FAQ | ★ Learning Check 交互提示 |
| 适用场景 | "帮我研究这些链接" | "帮我学习这篇文档" | "我想边研究边学" |

**路由规则：**
- 用户说"研究/分析/竞品/选型" → 研究模式
- 用户说"学习/笔记/知识卡片/深度阅读" → study 模式
- 用户说"边学边做/交互式学习/练习判断" → learning 输出风格（`--style=learning`）
- 不确定时询问："你需要知识卡片（study）、研究报告（默认）、还是交互式学习（learning）？"

### study 模式执行流程

1-4 步（提取、分类）与研究模式相同。
从第 5 步开始分叉：

5. **学习分析**：按 `references/study-lenses.md` 选择 lens，提取核心概念、关键论点、代码示例
6. **真理锚定**：通过 WebSearch 验证关键断言，标记 [已验证]/[存在争议]/[已过时]/[待确认]
7. **认知地图**：从概念中提取关系，生成 Mermaid 图（`scripts/linky/study.py:generate_cognitive_map`）
8. **FAQ 生成**：基于内容生成 5-8 个学习者会问的问题
9. **Markdown 笔记**：按 `references/output-styles/study.md` 模板组装
10. **HTML 卡片**：用 `scripts/linky/html_card.py` 渲染交互式卡片
11. **多源交叉分析**（仅多输入时）：识别共同概念、冲突观点、知识差距

### 触发条件

用户输入中出现以下关键词时路由到 study 模式：
- 中文：学习、深度阅读、做笔记、知识卡片、学习材料、学习笔记、帮我学
- 英文：study、learn、deep read、knowledge card、study notes

如果用户意图不明确，询问："这是研究分析（竞品/选型/情报）还是学习材料（深度笔记/知识卡片）？"

## 质量检查清单

完成报告前自检：
- [ ] 每个链接都已纳入报告（包括无法访问的和 pending 的）
- [ ] 每个链接都尝试了正文提取（已有预提取内容的除外）
- [ ] 不同类型使用了不同的分析模板
- [ ] 每个条目都有"我的判断"和"建议的后续行动"
- [ ] 没有空洞形容词，信息具体可比较
- [ ] 按类型分组而非按原始顺序排列
- [ ] 组内按研究价值排序
- [ ] 无法访问的链接有醒目标注
- [ ] 研究结论部分有实质性洞察
- [ ] 所有访问过的域名都更新了 `domains/{domain}.md`（含 trace）
- [ ] 需要用户确认的链接已呈现给用户并标注 pending 状态
- [ ] 受限内容没有被当作可访问内容处理
