from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


STANDARD_OUTPUT_STYLE = "standard"
MINIMAL_PLAIN_OUTPUT_STYLE = "minimal_plain"
EXPLANATORY_OUTPUT_STYLE = "explanatory"
LEARNING_OUTPUT_STYLE = "learning"
STUDY_OUTPUT_STYLE = "study"

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BUILTIN_STYLE_DIR = _REPO_ROOT / "references" / "output-styles"

_STYLE_ALIASES = {
    "": STANDARD_OUTPUT_STYLE,
    "default": STANDARD_OUTPUT_STYLE,
    "standard": STANDARD_OUTPUT_STYLE,
    "标准": STANDARD_OUTPUT_STYLE,
    "标准报告": STANDARD_OUTPUT_STYLE,
    "极简白话": MINIMAL_PLAIN_OUTPUT_STYLE,
    "minimal_plain": MINIMAL_PLAIN_OUTPUT_STYLE,
    "minimal-plain": MINIMAL_PLAIN_OUTPUT_STYLE,
    "plain": MINIMAL_PLAIN_OUTPUT_STYLE,
    "simple_plain": MINIMAL_PLAIN_OUTPUT_STYLE,
    "explanatory": EXPLANATORY_OUTPUT_STYLE,
    "Explanatory": EXPLANATORY_OUTPUT_STYLE,
    "解释型": EXPLANATORY_OUTPUT_STYLE,
    "解释": EXPLANATORY_OUTPUT_STYLE,
    "learning": LEARNING_OUTPUT_STYLE,
    "Learning": LEARNING_OUTPUT_STYLE,
    "学习型": LEARNING_OUTPUT_STYLE,
    "学习": LEARNING_OUTPUT_STYLE,
    "study": STUDY_OUTPUT_STYLE,
    "Study": STUDY_OUTPUT_STYLE,
    "study-card": STUDY_OUTPUT_STYLE,
    "study_card": STUDY_OUTPUT_STYLE,
    "学习卡片": STUDY_OUTPUT_STYLE,
    "知识卡片": STUDY_OUTPUT_STYLE,
}


def normalize_output_style(style: str | None) -> str:
    if style is None:
        return STANDARD_OUTPUT_STYLE
    key = str(style).strip()
    if not key:
        return STANDARD_OUTPUT_STYLE
    return _STYLE_ALIASES.get(key, _STYLE_ALIASES.get(key.lower(), key.lower().replace(" ", "-")))


@dataclass(frozen=True)
class OutputStyle:
    id: str
    name: str
    description: str = ""
    keep_research_instructions: bool = True
    render_mode: str = STANDARD_OUTPUT_STYLE
    instructions: str = ""
    source: str = "builtin"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _parse_bool(value: str | bool | None, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text.strip()
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text.strip()
    header = text[4:end]
    body = text[end + 4 :].strip()
    metadata: dict[str, str] = {}
    for line in header.splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, body


def _style_file_stems(style_id: str) -> list[str]:
    kebab = style_id.replace("_", "-")
    snake = style_id.replace("-", "_")
    stems = [style_id, kebab, snake]
    return list(dict.fromkeys(stems))


def _style_search_dirs(config_dir: str | Path | None = None) -> list[Path]:
    dirs: list[Path] = []
    if config_dir is None:
        config_dir = Path.home() / ".config" / "linky"
    config_path = Path(config_dir).expanduser()
    dirs.append(config_path / "output-styles")
    dirs.append(_BUILTIN_STYLE_DIR)
    return dirs


def _load_style_file(path: Path, style_id: str) -> OutputStyle:
    metadata, instructions = _parse_frontmatter(path.read_text(encoding="utf-8"))
    loaded_id = normalize_output_style(metadata.get("id") or style_id)
    render_mode = normalize_output_style(metadata.get("render-mode") or loaded_id)
    return OutputStyle(
        id=loaded_id,
        name=metadata.get("name") or loaded_id,
        description=metadata.get("description", ""),
        keep_research_instructions=_parse_bool(metadata.get("keep-research-instructions"), True),
        render_mode=render_mode,
        instructions=instructions,
        source=str(path),
    )


def load_output_style(style: str | None = None, config_dir: str | Path | None = None) -> OutputStyle:
    style_id = normalize_output_style(style)
    for directory in _style_search_dirs(config_dir):
        for stem in _style_file_stems(style_id):
            path = directory / f"{stem}.md"
            if path.exists():
                return _load_style_file(path, style_id)

    return OutputStyle(
        id=style_id,
        name=style_id,
        render_mode=MINIMAL_PLAIN_OUTPUT_STYLE if style_id == MINIMAL_PLAIN_OUTPUT_STYLE else STANDARD_OUTPUT_STYLE,
        source="fallback",
    )


def get_output_style_instructions(style: str | None = None, config_dir: str | Path | None = None) -> str:
    return load_output_style(style, config_dir).instructions


def _first_text(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [line.strip(" -") for line in value.splitlines() if line.strip(" -")]
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


@dataclass
class ReportItem:
    name: str
    url: str
    type: str
    access_status: str
    one_line: str
    judgment: str
    next_action: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReportData:
    title: str
    items: list[ReportItem] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    conclusions: list[str] = field(default_factory=list)
    output_style: str = STANDARD_OUTPUT_STYLE

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "items": [item.to_dict() for item in self.items],
            "summary": self.summary,
            "conclusions": self.conclusions,
            "output_style": normalize_output_style(self.output_style),
        }

    def to_markdown(self, output_style: str | None = None) -> str:
        style = load_output_style(output_style or self.output_style)
        if style.render_mode == MINIMAL_PLAIN_OUTPUT_STYLE:
            return self._to_minimal_plain_markdown()
        return self._to_standard_markdown()

    def _to_standard_markdown(self) -> str:
        lines = [f"# {self.title}", "", "## A. 研究总览", ""]
        lines.append(f"- 链接总数：{len(self.items)}")
        for key, value in self.summary.items():
            lines.append(f"- {key}：{value}")
        lines.extend(["", "## B. 分类型逐条整理", ""])

        for idx, item in enumerate(self.items, 1):
            lines.extend(
                [
                    f"### {idx}. {item.name}",
                    "",
                    f"- **链接**：{item.url}",
                    f"- **类型**：{item.type}",
                    f"- **访问状态**：{item.access_status}",
                    f"- **一句话结论**：{item.one_line}",
                    "",
                    "#### 我的判断",
                    f"- {item.judgment}",
                    "",
                    "#### 建议的后续行动",
                    f"- {item.next_action}",
                    "",
                ]
            )

        lines.extend(["## C. 研究结论", ""])
        if self.conclusions:
            lines.extend(f"- {item}" for item in self.conclusions)
        else:
            lines.append("- 暂无额外结论。")
        return "\n".join(lines).rstrip() + "\n"

    def _to_minimal_plain_markdown(self) -> str:
        if not self.items:
            return (
                "1.【结论】暂无内容。\n\n"
                "2.【具体讲了啥】\n暂无。\n\n"
                "3.【关键点】\n- 暂无。\n\n"
                "4.【对我有什么用】\n暂无。\n\n"
                "5.【原链接】\n无\n"
            )

        blocks: list[str] = []
        multiple_items = len(self.items) > 1
        for idx, item in enumerate(self.items, 1):
            if multiple_items:
                blocks.extend([f"## {idx}. {item.name}", ""])

            conclusion = _first_text(item.one_line, item.judgment, "暂无明确结论。")
            context = _first_text(
                item.metadata.get("plain_context"),
                item.metadata.get("what_it_says"),
                item.metadata.get("具体讲了啥"),
                item.judgment,
                "暂无更多内容。",
            )
            key_points = _as_list(
                item.metadata.get("key_points")
                or item.metadata.get("highlights")
                or item.metadata.get("关键点")
            )
            if not key_points:
                key_points = [context]
            usefulness = _first_text(
                item.metadata.get("usefulness"),
                item.metadata.get("value_for_me"),
                item.metadata.get("对我有什么用"),
                item.next_action,
                "暂时看不出明确价值。",
            )

            blocks.extend(
                [
                    f"1.【结论】{conclusion}",
                    "",
                    "2.【具体讲了啥】",
                    context,
                    "",
                    "3.【关键点】",
                    *[f"- {point}" for point in key_points],
                    "",
                    "4.【对我有什么用】",
                    usefulness,
                    "",
                    "5.【原链接】",
                    item.url,
                ]
            )
            if idx != len(self.items):
                blocks.append("")

        return "\n".join(blocks).rstrip() + "\n"
