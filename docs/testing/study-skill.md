# Testing Matrix: study-skill

## Source
- Feature spec: ../features/study-skill.md
- Standard test cases: ../test-cases/study-skill.md

## Coverage Matrix

| Requirement | Test Case | Automated? | Command / Evidence |
|---|---|---|---|
| 单 URL 知识卡片生成 | TC1 | manual | `/study <url>` → 检查 `.md` + `.html` 存在且内容非空 |
| 多 URL 并发处理 | TC2 | manual | `/study <url1> <url2> <url3>` → 检查每个输出文件 + `cross-analysis.md` |
| 本地 PDF 学习 | TC3 | manual | `/study ./sample.pdf` → 检查输出 |
| 类型自适应 | TC4 | manual | 对比技术博客 vs 论文的输出格式差异 |
| 真理锚定标记 | TC5 | manual | 检查输出中是否包含 [存在争议]/[待确认] 标签 |
| 认知地图质量 | TC6 | manual | 检查 `.html` 中 Mermaid 图是否正确渲染 |
| 不可访问 URL 处理 | TC7 | auto | 脚本：传入已知 404 URL，检查输出标记为受限 |
| 超大文档分块 | TC8 | manual | 传入 100+ 页 PDF，检查是否分块产出 |
| HTML 离线可用 | TC9 | auto | 断言：grep 检查 `.html` 中无外部 CDN 引用 |
| Mermaid 语法修正 | TC10 | auto | 断言：对比输入 Mermaid 和输出 Mermaid 的语法差异 |
| linky 共存 | TC11 | auto | 断言：检查输出目录不与 linky 冲突 |

## P0 Blockers

- None

## Release Gates

- Gate 1: TC1-TC6 全部通过（核心功能）
- Gate 2: TC9 通过（HTML 离线可用 —— 安全性）
- Gate 3: TC11 通过（linky 共存 —— 生态兼容）
