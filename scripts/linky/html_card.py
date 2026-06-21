from __future__ import annotations

import html
from pathlib import Path
from typing import Any


_TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "references"
_TEMPLATE_FILE = _TEMPLATE_DIR / "study-html-template.html"


def _escape(text: str) -> str:
    return html.escape(str(text), quote=True)


def _render_concepts(concepts: list[dict[str, str]]) -> str:
    parts = []
    for c in concepts:
        name = _escape(c.get("name", ""))
        definition = _escape(c.get("definition", ""))
        parts.append(f'<div class="concept card"><h3>{name}</h3><p>{definition}</p></div>')
    return "\n".join(parts)


def _render_faq(faq: list[dict[str, str]]) -> str:
    parts = []
    for i, q in enumerate(faq, 1):
        question = _escape(q.get("question", ""))
        answer = _escape(q.get("answer", ""))
        parts.append(f'<div class="faq-item"><h3>Q{i}: {question}</h3><p>{answer}</p></div>')
    return "\n".join(parts)


def _render_claims(claims: list[dict[str, str]]) -> str:
    parts = []
    for c in claims:
        claim = _escape(c.get("claim", ""))
        tag = _escape(c.get("tag", "待确认"))
        evidence = _escape(c.get("evidence", ""))
        tag_class = {
            "已验证": "tag-verified", "存在争议": "tag-disputed",
            "已过时": "tag-outdated", "待确认": "tag-pending",
        }.get(tag, "tag-pending")
        parts.append(f'<div class="claim"><span class="tag {tag_class}">{tag}</span> {claim} — {evidence}</div>')
    return "\n".join(parts)


def _render_code_examples(examples: list[dict[str, str]]) -> str:
    parts = []
    for ex in examples:
        lang = _escape(ex.get("language", "text"))
        code = _escape(ex.get("code", ""))
        annotation = _escape(ex.get("annotation", ""))
        parts.append(f'<pre><code class="language-{lang}">{code}</code></pre>')
        if annotation:
            parts.append(f'<p class="code-annotation">{annotation}</p>')
    return "\n".join(parts)


def render_html_card(data: dict[str, Any]) -> str:
    """Render an interactive HTML knowledge card from structured data."""
    template = _TEMPLATE_FILE.read_text(encoding="utf-8")

    replacements = {
        "{{TITLE}}": _escape(data.get("title", "Untitled")),
        "{{SOURCE_URL}}": _escape(data.get("source_url", "")),
        "{{CONTENT_TYPE}}": _escape(data.get("content_type", "general")),
        "{{DATE}}": _escape(data.get("date", "")),
        "{{OVERVIEW}}": _escape(data.get("overview", "")),
        "{{CONCEPTS}}": _render_concepts(data.get("concepts", [])),
        "{{COGNITIVE_MAP}}": data.get("cognitive_map", ""),
        "{{FAQ}}": _render_faq(data.get("faq", [])),
        "{{CODE_EXAMPLES}}": _render_code_examples(data.get("code_examples", [])),
        "{{CLAIMS}}": _render_claims(data.get("claims", [])),
        "{{FURTHER_READING}}": "\n".join(
            f'<li><a href="{_escape(r.get("url", ""))}">{_escape(r.get("title", ""))}</a></li>'
            for r in data.get("further_reading", [])
        ),
        "{{MERMAID_JS}}": "/* Mermaid.js inline bundle — see references/study-html-template.html */",
        "{{PRISM_JS}}": "/* Prism.js inline bundle — see references/study-html-template.html */",
    }

    result = template
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)

    return result
