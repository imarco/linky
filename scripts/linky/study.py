from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse


def classify_content_type(url: str, metadata: dict[str, Any]) -> str:
    """Classify content into a study lens type based on URL and metadata."""
    domain = urlparse(url).netloc.lower().removeprefix("www.")

    if "github.com" in domain or "gitlab.com" in domain:
        return "technical"
    if "arxiv.org" in domain:
        return "academic"
    if any(d in domain for d in ["medium.com", "dev.to", "hashnode"]):
        return "blog"
    if any(d in domain for d in ["docs.", "documentation", "readthedocs"]):
        return "tutorial"

    # Fallback: check metadata hints
    title = metadata.get("title", "").lower()
    if any(w in title for w in ["paper", "study", "research", "analysis"]):
        return "academic"
    if any(w in title for w in ["tutorial", "guide", "how to", "step"]):
        return "tutorial"
    if any(w in title for w in ["blog", "post", "article"]):
        return "blog"

    return "technical"


_STRUCTURAL_HEADINGS = {
    # English
    "introduction", "intro", "overview", "background", "summary", "conclusion",
    "conclusions", "table of contents", "toc", "references", "bibliography",
    "acknowledgments", "acknowledgements", "appendix", "appendices", "footnotes",
    "about the author", "about", "preface", "foreword", "abstract", "discussion",
    "results", "methods", "methodology", "related work", "future work",
    # Chinese
    "目录", "前言", "序言", "引言", "简介", "概述", "背景", "总结", "结论",
    "参考资料", "参考文献", "致谢", "附录", "脚注", "关于作者", "关于",
    "讨论", "结果", "方法", "方法论", "相关工作", "未来工作",
}


def extract_concepts(markdown: str) -> list[dict[str, str]]:
    """Extract key concepts from markdown content.

    Uses heading-based extraction: h1/h2/h3 headings become concept names,
    the following paragraph becomes the definition.
    Structural headings (Introduction, Summary, etc.) are filtered out.

    Known limitation: this is a simple heuristic. Real-world content may have
    meaningful concepts as non-heading text, or structural headings that ARE
    the concept (e.g., a section called "Redis Caching" is both structural
    and a concept). Post-v1: upgrade to NLP-based extraction.
    """
    concepts = []
    lines = markdown.split("\n")
    current_concept = None
    current_def_lines: list[str] = []

    for line in lines:
        heading_match = re.match(r"^#{1,3}\s+(.+)$", line.strip())
        if heading_match:
            # Save previous concept
            if current_concept:
                definition = "\n".join(current_def_lines).strip()
                if definition:
                    concepts.append({"name": current_concept, "definition": definition[:500]})

            heading_text = heading_match.group(1).strip()
            # Filter out structural headings that aren't real concepts
            if heading_text.lower().strip() in _STRUCTURAL_HEADINGS:
                current_concept = None
                current_def_lines = []
            else:
                current_concept = heading_text
                current_def_lines = []
        elif current_concept and line.strip():
            current_def_lines.append(line.strip())

    # Save last concept
    if current_concept:
        definition = "\n".join(current_def_lines).strip()
        if definition:
            concepts.append({"name": current_concept, "definition": definition[:500]})

    return concepts[:15]  # Cap at 15 concepts


def generate_cognitive_map(concepts: list[dict[str, str]]) -> str:
    """Generate a Mermaid graph showing concept relationships."""
    if len(concepts) < 2:
        return "graph LR\n  A[No concepts extracted]"

    lines = ["graph LR"]
    # Create nodes
    for i, c in enumerate(concepts[:10]):  # Cap at 10 for readability
        node_id = f"C{i}"
        name = c["name"][:30].replace("[", "(").replace("]", ")")
        lines.append(f"  {node_id}[{name}]")

    # Create sequential edges (simple heuristic: concepts in order relate)
    for i in range(len(concepts[:10]) - 1):
        lines.append(f"  C{i} --> C{i+1}")

    return "\n".join(lines)


def generate_faq(markdown: str, title: str) -> list[dict[str, str]]:
    """Generate FAQ items from content analysis.

    Produces template-based FAQs. The SKILL.md instructs the AI agent
    to refine these with real content-aware questions.
    """
    faqs = [
        {"question": f"What is {title}?", "answer": "See the Overview section above."},
        {"question": "What are the key concepts?", "answer": "See the Core Concepts section."},
        {"question": "What prerequisites do I need?", "answer": "See the Prerequisites section."},
        {"question": "Are the claims verified?", "answer": "See the Claims & Evidence section."},
    ]
    return faqs


def build_study_card_data(extraction: dict[str, Any]) -> dict[str, Any]:
    """Build structured data for study card generation from an extraction result.

    DATA FLOW CONTRACT:
    Fields below are split between Python code and AI agent (via SKILL.md instructions).
    This is a deliberate design choice for v1 — code handles structured extraction,
    agent handles semantic analysis that requires LLM reasoning.

    CODE-DRIVEN (Python fills these):
      title, source_url, content_type, date, overview, concepts, cognitive_map, faq

    AGENT-DRIVEN (SKILL.md instructs the AI agent to fill these after card generation):
      code_examples — agent extracts and annotates code samples from the full content
      claims        — agent identifies key claims and verifies via WebSearch (truth anchoring)
      further_reading — agent suggests related resources based on content analysis
    """
    url = extraction.get("url", "")
    markdown = extraction.get("markdown", "")
    metadata = extraction.get("metadata", {})

    title = metadata.get("title") or _title_from_url(url)
    content_type = classify_content_type(url, metadata)
    concepts = extract_concepts(markdown)
    cognitive_map = generate_cognitive_map(concepts)
    faq = generate_faq(markdown, title)

    return {
        # CODE-DRIVEN fields
        "title": title,
        "source_url": url,
        "content_type": content_type,
        "date": metadata.get("date", ""),
        "overview": markdown[:300] + "..." if len(markdown) > 300 else markdown,
        "concepts": concepts,
        "cognitive_map": cognitive_map,
        "faq": faq,
        # AGENT-DRIVEN fields (populated by AI agent via SKILL.md, not by Python)
        "code_examples": [],  # agent fills: [{language, code, annotation}]
        "claims": [],         # agent fills: [{claim, tag, evidence}]  (truth anchoring)
        "further_reading": [],  # agent fills: [{url, title}]
    }


def _title_from_url(url: str) -> str:
    """Extract a reasonable title from a URL path."""
    path = urlparse(url).path.rstrip("/")
    if "/" in path:
        return path.split("/")[-1].replace("-", " ").replace("_", " ").title()
    return urlparse(url).netloc
