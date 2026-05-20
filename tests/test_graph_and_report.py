import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from linky.graph import ResearchGraph
from linky.report import (
    ReportData,
    ReportItem,
    get_output_style_instructions,
    load_output_style,
    normalize_output_style,
)


class GraphAndReportTests(unittest.TestCase):
    def test_research_graph_deduplicates_nodes_and_edges(self):
        graph = ResearchGraph()
        graph.add_node("topic:agents", "topic", "Agents", {"count": 1})
        graph.add_node("topic:agents", "topic", "Agents", {"last_seen": "today"})
        graph.add_node("url:https://example.com", "url", "Example")
        graph.add_edge("url:https://example.com", "topic:agents", "mentions", {"source": "a"})
        graph.add_edge("url:https://example.com", "topic:agents", "mentions", {"source": "b"})

        data = graph.to_dict()

        self.assertEqual(len(data["nodes"]), 2)
        self.assertEqual(len(data["edges"]), 1)
        topic = graph.nodes["topic:agents"]
        self.assertEqual(topic.metadata["count"], 1)
        self.assertEqual(topic.metadata["last_seen"], "today")
        edge = next(iter(graph.edges.values()))
        self.assertEqual(edge.metadata["source"], "b")

    def test_report_data_renders_markdown_sections(self):
        report = ReportData(
            title="链接研究报告",
            items=[
                ReportItem(
                    name="Example",
                    url="https://example.com",
                    type="文章",
                    access_status="✅ 正常",
                    one_line="A useful example.",
                    judgment="Worth reading.",
                    next_action="Read source.",
                )
            ],
            conclusions=["Keep this source."],
        )

        markdown = report.to_markdown()

        self.assertIn("## A. 研究总览", markdown)
        self.assertIn("## B. 分类型逐条整理", markdown)
        self.assertIn("## C. 研究结论", markdown)
        self.assertIn("#### 建议的后续行动", markdown)

    def test_report_data_renders_minimal_plain_style_from_report_setting(self):
        report = ReportData(
            title="视频解释",
            output_style="极简白话",
            items=[
                ReportItem(
                    name="Example Video",
                    url="https://example.com/video",
                    type="视频",
                    access_status="✅ 正常",
                    one_line="这个视频说少做无效整理，直接抓重点。",
                    judgment="作者先讲问题，再讲怎么快速判断值不值得看。",
                    next_action="值得看前五分钟，后面可以跳过。",
                    metadata={
                        "plain_context": "先说很多人看视频浪费时间，再说要先看结论和例子。",
                        "key_points": ["别从头硬看。", "先找结论。", "没干货就退出。"],
                        "usefulness": "能帮你更快筛掉水视频。",
                    },
                )
            ],
        )

        markdown = report.to_markdown()

        self.assertNotIn("## A. 研究总览", markdown)
        self.assertIn("1.【结论】这个视频说少做无效整理，直接抓重点。", markdown)
        self.assertIn("2.【具体讲了啥】", markdown)
        self.assertIn("- 别从头硬看。", markdown)
        self.assertIn("4.【对我有什么用】", markdown)
        self.assertIn("5.【原链接】\nhttps://example.com/video", markdown)

    def test_report_data_renders_minimal_plain_style_from_call_override(self):
        report = ReportData(
            title="链接研究报告",
            items=[
                ReportItem(
                    name="Example",
                    url="https://example.com",
                    type="文章",
                    access_status="✅ 正常",
                    one_line="直接讲一个有用观点。",
                    judgment="它说要先做选择，再投入时间。",
                    next_action="可以留着做选题参考。",
                )
            ],
        )

        markdown = report.to_markdown(output_style="minimal_plain")

        self.assertIn("1.【结论】直接讲一个有用观点。", markdown)
        self.assertNotIn("#### 我的判断", markdown)

    def test_builtin_explanatory_style_loads_prompt_instructions(self):
        style = load_output_style("Explanatory")

        self.assertEqual(style.id, "explanatory")
        self.assertEqual(style.render_mode, "standard")
        self.assertTrue(style.keep_research_instructions)
        self.assertIn("educational insights", style.instructions)
        self.assertIn("★ Insight", get_output_style_instructions("explanatory"))

    def test_builtin_learning_style_loads_prompt_instructions(self):
        style = load_output_style("Learning")

        self.assertEqual(style.id, "learning")
        self.assertEqual(style.render_mode, "standard")
        self.assertIn("Learning Mode Philosophy", style.instructions)
        self.assertIn("★ Learning Check", style.instructions)

    def test_output_style_aliases_include_explanatory_and_learning(self):
        self.assertEqual(normalize_output_style("解释型"), "explanatory")
        self.assertEqual(normalize_output_style("学习型"), "learning")
        self.assertEqual(normalize_output_style("极简白话"), "minimal_plain")

    def test_explanatory_and_learning_keep_standard_renderer(self):
        report = ReportData(
            title="链接研究报告",
            items=[
                ReportItem(
                    name="Example",
                    url="https://example.com",
                    type="文章",
                    access_status="✅ 正常",
                    one_line="直接讲一个有用观点。",
                    judgment="它说要先做选择，再投入时间。",
                    next_action="可以留着做选题参考。",
                )
            ],
        )

        explanatory = report.to_markdown(output_style="explanatory")
        learning = report.to_markdown(output_style="learning")

        self.assertIn("## A. 研究总览", explanatory)
        self.assertIn("#### 我的判断", explanatory)
        self.assertIn("## A. 研究总览", learning)
        self.assertIn("#### 我的判断", learning)

    def test_user_output_style_file_overrides_builtin_style(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            styles_dir = Path(tmpdir) / "output-styles"
            styles_dir.mkdir()
            custom_style = styles_dir / "explanatory.md"
            custom_style.write_text(
                """---
id: explanatory
name: Custom Explanatory
description: User override
keep-research-instructions: true
render-mode: standard
---

Custom user instructions.
""",
                encoding="utf-8",
            )

            style = load_output_style("explanatory", config_dir=tmpdir)

        self.assertEqual(style.name, "Custom Explanatory")
        self.assertEqual(style.instructions, "Custom user instructions.")
        self.assertIn(str(custom_style), style.source)


if __name__ == "__main__":
    unittest.main()
