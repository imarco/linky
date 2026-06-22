# Standard Test Cases: study-skill

## Source
- Feature spec: ../features/study-skill.md

## Acceptance Tests

1. **单 URL 学习卡片生成**：给定一个技术博客 URL，产出完整的 `.md` 笔记 + `.interactive.html` 知识卡片，卡片包含搜索、Mermaid 图、代码高亮
2. **多 URL 并发处理**：给定 3-5 个相关技术文章 URL，每个 URL 独立产出知识卡片，并额外产出 `cross-analysis.md` 交叉分析
3. **本地 PDF 学习**：给定一个本地 PDF 文件路径，正确提取内容并产出知识卡片
4. **类型自适应**：技术文档 vs 论文 vs 博客，输出风格和分析框架应有明显差异
5. **真理锚定**：对于包含争议性技术断言的内容，在笔记中标注 [存在争议] 或 [待确认] 标签
6. **认知地图质量**：Mermaid 图正确渲染，概念关系准确，节点数量合理（5-15 个核心概念）

## Edge Cases

7. **不可访问 URL**：URL 返回 404 或需要登录，应标记为受限状态并继续处理其他输入
8. **超大文档**：100+ 页 PDF，应分块处理，产出摘要 + 详细章节笔记
9. **纯图片/PDF 扫描件**：需要 OCR 能力，标记为受限或使用 image 分析
10. **混合输入**：同时包含 URL 和本地文件的输入列表，应统一处理

## Regression Tests

11. **linky 兼容性**：skill 在 linky 已安装的环境中不产生冲突（输出目录、配置文件不冲突）
12. **HTML 卡片离线可用**：生成的 `.interactive.html` 不依赖外部 CDN，所有资源内联
13. **Mermaid 语法修正**：自动修正常见的 Mermaid 语法错误，确保图表在浏览器中正确渲染
