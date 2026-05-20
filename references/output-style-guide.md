# 输出风格指南

输出风格控制报告的口吻、长度和段落结构；输出方式控制报告投递到哪里。两者互不替代：

- 输出方式：Markdown、Obsidian、Notion、Yinxiang、Prompt 模式等。
- 输出风格：standard、极简白话、explanatory、learning、用户自定义风格等。

默认输出风格是 `standard`，保持 A/B/C 研究报告结构不变。

---

## 风格定义文件

Linky 的风格定义借鉴 Claude Code：一个 Markdown 文件包含 frontmatter 和正文指令。

内置风格位于 `references/output-styles/*.md`。用户自定义风格位于 `~/.config/linky/output-styles/*.md`，同名文件优先于内置风格。

```markdown
---
id: minimal_plain
name: 极简白话
description: 最短白话解释，适合视频和低耐心阅读
keep-research-instructions: true
render-mode: minimal_plain
---

这里写追加给 Linky 的输出风格指令。
```

frontmatter 字段：

- `id`：稳定 ID。
- `name`：显示名。
- `description`：给选择器或文档展示的短说明。
- `keep-research-instructions`：是否保留 Linky 的正文提取、分类、分析规则。默认 `true`。
- `render-mode`：最终 Markdown 渲染模式。默认等于 `id`；目前 `standard` 和 `minimal_plain` 有独立渲染行为，其他风格默认走标准报告渲染。

---

## 内置风格

### standard

默认研究报告风格。保留：

- A. 研究总览
- B. 分类型逐条整理
- C. 研究结论

适合批量研究、资料筛选、选题库、产品/技术调研。

### 极简白话

稳定 id / alias：

- `极简白话`
- `minimal_plain`
- `minimal-plain`

适合用户想快速知道“这到底在说什么、值不值得看”的场景，尤其适合视频链接。

输出顺序：

1.【结论】直接说核心意思。

2.【具体讲了啥】用极简白话说明来龙去脉。

3.【关键点】列出最重要的几个要点。

4.【对我有什么用】直接说明价值；如果是纯广告或水内容，直接说避雷。

5.【原链接】附上原始链接。

### explanatory

借鉴 Claude Code Explanatory：在完成研究报告的同时，补充简短 insight，解释判断依据、信息质量和取舍。

适合学习 Linky 的判断过程、训练选题/产品/技术分析眼光。

### learning

借鉴 Claude Code Learning：让用户参与少量关键判断，而不是只被动接收报告。

适合用户想训练自己的筛选、判断、拆解能力时使用。该风格不适合无人值守批处理。

---

## 配置示例

```toml
default_output = "markdown"
output_style = "极简白话"
```

或：

```toml
default_output = "obsidian"
output_style = "explanatory"
```
