# Task Plan: study-skill

## Meta
- Subproject: study-skill
- Created: 2026-06-19
- Owner: marco
- Base branch: main
- Feature branch: main

## Goal

Extend linky with `--mode=study` to produce structured learning materials (Markdown deep notes + interactive HTML knowledge cards) instead of research reports.

## Architecture Summary

Add a `study` output mode to linky's existing pipeline. After extraction and classification (shared with research mode), the study mode diverges at the analysis and output stages: it applies learning-oriented analysis lenses, generates knowledge cards with cognitive maps, performs truth anchoring via web search, and renders interactive HTML cards. All new code lives in the linky repo (`/Users/marco/Documents/code.nosync/ai/linky/`).

**Tech Stack:** Python 3.8+ (linky standard), HTML/CSS/JS (knowledge card template), Mermaid.js (cognitive maps, inline), Prism.js (code highlighting, inline)

## Source Docs
- Feature spec: docs/features/study-skill.md
- Standard test cases: docs/test-cases/study-skill.md
- Testing matrix: docs/testing/study-skill.md
- Roadmap: docs/plans/roadmap.md
- Current status: docs/plans/current-status.md

## Current Phase
Shipped

## Phases

### Phase 1: Foundation — Output Style + Lenses
- **Status:** complete
- **Verification command:** `cd /Users/marco/Documents/code.nosync/ai/linky && python3 -m pytest tests/test_study_mode.py -v`
- **Discipline:** tdd
- **Files:** scripts/linky/report.py, references/output-styles/study.md, references/study-lenses.md, tests/test_study_mode.py
- **Tasks:**

---

## File Structure

```
linky/
├── SKILL.md                                    # Modify: add study mode trigger + workflow section
├── references/
│   ├── output-styles/study.md                  # Create: study mode output style definition
│   ├── study-lenses.md                         # Create: 4 learning analysis lenses (technical/academic/blog/tutorial)
│   ├── study-card-template.md                  # Create: Markdown knowledge card template
│   └── study-html-template.html                # Create: interactive HTML knowledge card template
├── scripts/linky/
│   ├── study.py                                # Create: study mode pipeline (truth anchoring, cognitive map, cross-analysis)
│   ├── html_card.py                            # Create: HTML card generator (renders from template + data)
│   └── report.py                               # Modify: add STUDY_OUTPUT_STYLE constant + study render path
└── tests/
    ├── test_study_mode.py                      # Create: study mode pipeline tests
    └── test_html_card.py                       # Create: HTML card generator tests
```

---

### Task 1: Add `study` output style constant to report.py

**Files:**
- Modify: `scripts/linky/report.py`
- Test: `tests/test_study_mode.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_study_mode.py
from scripts.linky.report import normalize_output_style, STUDY_OUTPUT_STYLE


def test_study_style_constant():
    assert STUDY_OUTPUT_STYLE == "study"


def test_normalize_study_aliases():
    assert normalize_output_style("study") == "study"
    assert normalize_output_style("学习卡片") == "study"
    assert normalize_output_style("知识卡片") == "study"
    assert normalize_output_style("study-card") == "study"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/marco/Documents/code.nosync/ai/linky && python3 -m pytest tests/test_study_mode.py -v`
Expected: FAIL — `STUDY_OUTPUT_STYLE` not defined, aliases not in `_STYLE_ALIASES`

- [ ] **Step 3: Write minimal implementation**

In `scripts/linky/report.py`, add the constant and aliases:

```python
# After LEARNING_OUTPUT_STYLE = "learning"
STUDY_OUTPUT_STYLE = "study"
```

In `_STYLE_ALIASES`, add:

```python
"study": STUDY_OUTPUT_STYLE,
"study-card": STUDY_OUTPUT_STYLE,
"study_card": STUDY_OUTPUT_STYLE,
"学习卡片": STUDY_OUTPUT_STYLE,
"知识卡片": STUDY_OUTPUT_STYLE,
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/marco/Documents/code.nosync/ai/linky && python3 -m pytest tests/test_study_mode.py::test_study_style_constant tests/test_study_mode.py::test_normalize_study_aliases -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/marco/Documents/code.nosync/ai/linky
git add scripts/linky/report.py tests/test_study_mode.py
git commit -m "feat(study): add study output style constant and aliases to report.py"
```

---

### Task 2: Create study output style definition

**Files:**
- Create: `references/output-styles/study.md`

- [ ] **Step 1: Create the study output style file**

```markdown
---
id: study
name: Study Knowledge Card
description: Learning-focused mode that produces structured study materials with knowledge cards, cognitive maps, and truth anchoring
keep-research-instructions: false
render-mode: study
---

You are in `study` output style mode for Linky.

This mode produces **learning materials** instead of research reports. The goal is
deep understanding, not decision support.

## Study Mode Philosophy

Transform raw content into structured knowledge that supports learning, retention,
and review. Every output should help the reader understand, remember, and apply
the material.

## Analysis Framework

Apply these lenses in order:

1. **Core Concepts** — What are the 3-7 most important ideas? Define each clearly.
2. **Prerequisite Knowledge** — What does the reader need to know first?
3. **Key Arguments/Claims** — What does the author assert? What evidence supports it?
4. **Code/Examples** — Extract and annotate any code samples or practical examples.
5. **Concept Relationships** — How do the concepts relate to each other? (→ Mermaid cognitive map)
6. **Critical Assessment** — What's strong? What's weak? What's missing?
7. **FAQ Generation** — Generate 5-8 questions a learner would ask, with answers.

## Truth Anchoring Protocol

Do not trust claims blindly. For each key claim:
- If verifiable via web search, verify it and note the result
- Tag with: [已验证], [存在争议], [已过时], [待确认]
- If the claim involves version numbers, dates, or statistics — verify

## Output Format

Produce TWO outputs per source:

### 1. Markdown Deep Notes (`<name>.md`)

```
# <Title>

> Source: <URL> | Type: <content-type> | Date: <extraction-date>
> Verified: <N> claims | Tagged: [争议:<N>] [过时:<N>] [待确认:<N>]

## Overview
<2-3 sentence summary>

## Core Concepts
### <Concept 1>
<definition, explanation, examples>

### <Concept 2>
...

## Prerequisites
<what the reader should know first>

## Key Claims & Evidence
- **Claim**: <text> — [已验证/存在争议/已过时/待确认] <evidence>

## Code Examples
<annotated code blocks>

## Cognitive Map
```mermaid
<concept relationship diagram>
```

## FAQ
**Q1**: <question>
**A1**: <answer>
...

## Critical Assessment
### Strengths
- ...
### Weaknesses
- ...
### What's Missing
- ...

## Further Reading
- <related links>
```

### 2. Interactive HTML Knowledge Card (`<name>.interactive.html`)

See `references/study-html-template.html` for the template.

## Multi-Source Cross-Analysis (when multiple inputs)

When processing multiple sources, additionally produce:

### Cross-Analysis (`cross-analysis.md`)
- **Shared Concepts**: ideas that appear across multiple sources
- **Conflicting Views**: where sources disagree (with citations)
- **Knowledge Gaps**: what's missing from the combined set
- **Recommended Learning Path**: suggested reading order with rationale
```

- [ ] **Step 2: Verify file is valid Markdown with correct frontmatter**

Run: `cd /Users/marco/Documents/code.nosync/ai/linky && python3 -c "from scripts.linky.report import load_output_style; s = load_output_style('study'); print(s.id, s.name, s.render_mode)"`
Expected: `study Study Knowledge Card study`

- [ ] **Step 3: Commit**

```bash
cd /Users/marco/Documents/code.nosync/ai/linky
git add references/output-styles/study.md
git commit -m "feat(study): add study output style definition"
```

---

### Task 3: Create learning analysis lenses reference

**Files:**
- Create: `references/study-lenses.md`

- [ ] **Step 1: Create the study lenses file**

Create `references/study-lenses.md` with 4 learning analysis lenses:

```markdown
# Study Analysis Lenses

Each content type gets a specialized analysis lens. After classification,
select the matching lens and apply its framework.

## Technical Documentation Lens

For: API docs, framework docs, library READMEs, configuration guides

Focus areas:
- **Interface contract**: What does the API expose? Parameters, return types, error modes
- **Usage patterns**: Common code patterns, gotchas, best practices
- **Version sensitivity**: Which version introduced this? Deprecated in what version?
- **Integration points**: How does this connect to other tools/frameworks?
- **Performance implications**: Memory, CPU, network characteristics

## Academic/Research Paper Lens

For: arXiv papers, journal articles, conference proceedings, thesis

Focus areas:
- **Research question**: What problem does this address?
- **Methodology**: How was the research conducted?
- **Key findings**: What did they discover? With what confidence?
- **Limitations**: What did the authors acknowledge as limitations?
- **Reproducibility**: Can the results be reproduced? Is code/data available?
- **Related work**: How does this relate to prior research?

## Technical Blog Lens

For: Medium articles, dev.to posts, personal blogs, company engineering blogs

Focus areas:
- **Problem context**: What real-world problem triggered this post?
- **Solution approach**: What was tried? What worked?
- **Code quality**: Is the code production-ready? What's missing?
- **Author credibility**: What's the author's background? Are claims backed?
- **Applicability**: When should you use this approach vs alternatives?

## Tutorial/Guide Lens

For: Step-by-step guides, how-to articles, video tutorials, workshops

Focus areas:
- **Prerequisites**: What should you know/have before starting?
- **Step completeness**: Are all steps explicit? Any skipped?
- **Verification points**: How do you know each step worked?
- **Common pitfalls**: What typically goes wrong at each step?
- **Customization**: What can you change? What's fixed?
```

- [ ] **Step 2: Commit**

```bash
cd /Users/marco/Documents/code.nosync/ai/linky
git add references/study-lenses.md
git commit -m "feat(study): add learning analysis lenses reference"
```

---

### Phase 2: Card Generation — HTML Template + Markdown Template
- **Status:** complete
- **Verification command:** `cd /Users/marco/Documents/code.nosync/ai/linky && python3 -m pytest tests/test_html_card.py -v`
- **Discipline:** tdd
- **Files:** references/study-html-template.html, scripts/linky/html_card.py, references/study-card-template.md, tests/test_html_card.py
- **Tasks:**

### Task 4: Create HTML knowledge card template

**Files:**
- Create: `references/study-html-template.html`
- Create: `tests/test_html_card.py`

- [ ] **Step 1: Write the failing test for HTML card generator**

```python
# tests/test_html_card.py
import tempfile
from pathlib import Path
from scripts.linky.html_card import render_html_card


def test_render_html_card_basic():
    data = {
        "title": "Test Card",
        "source_url": "https://example.com",
        "content_type": "technical",
        "date": "2026-06-19",
        "overview": "A test overview.",
        "concepts": [
            {"name": "Concept A", "definition": "Definition of A"}
        ],
        "cognitive_map": "graph LR\n  A --> B",
        "faq": [
            {"question": "What is this?", "answer": "A test."}
        ],
        "code_examples": [],
        "claims": [],
        "further_reading": [],
    }
    html = render_html_card(data)
    assert "<!DOCTYPE html>" in html
    assert "Test Card" in html
    assert "Concept A" in html
    assert "mermaid" in html.lower()
    assert "cdn" not in html.lower()  # offline requirement
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/marco/Documents/code.nosync/ai/linky && python3 -m pytest tests/test_html_card.py -v`
Expected: FAIL — `html_card` module doesn't exist

- [ ] **Step 3: Create the HTML template**

Create `references/study-html-template.html` — a self-contained HTML template with:
- Inline CSS for dark/light mode, layout, code highlighting
- Inline Mermaid.js (minified, ~1MB) for cognitive maps
- Search/filter JS that hides non-matching content blocks
- Sidebar TOC navigation
- Template placeholders: `{{TITLE}}`, `{{SOURCE_URL}}`, `{{DATE}}`, `{{OVERVIEW}}`, `{{CONCEPTS}}`, `{{COGNITIVE_MAP}}`, `{{FAQ}}`, `{{CODE_EXAMPLES}}`, `{{CLAIMS}}`, `{{FURTHER_READING}}`

Key constraints:
- ALL resources inline (no CDN) — offline requirement from P4
- Mermaid.js included as inline `<script>` (download minified bundle)
- Prism.js included as inline `<script>` + CSS for code highlighting
- Search JS: filter content blocks by keyword, hide non-matching `<section>` elements
- Dark/light mode: CSS `prefers-color-scheme` + toggle button

- [ ] **Step 4: Create the HTML card generator**

Create `scripts/linky/html_card.py`:

```python
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
        parts.append(f'<div class="concept"><h3>{name}</h3><p>{definition}</p></div>')
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
        parts.append(f'<div class="claim"><span class="tag">{tag}</span> {claim} — {evidence}</div>')
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
    }

    result = template
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)

    return result
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /Users/marco/Documents/code.nosync/ai/linky && python3 -m pytest tests/test_html_card.py -v`
Expected: PASS (requires the template file to exist from Step 3)

- [ ] **Step 6: Commit**

```bash
cd /Users/marco/Documents/code.nosync/ai/linky
git add references/study-html-template.html scripts/linky/html_card.py tests/test_html_card.py
git commit -m "feat(study): add HTML knowledge card template and generator"
```

---

### Phase 3: Study Pipeline — Classification + Cognitive Map + FAQ
- **Status:** complete
- **Verification command:** `cd /Users/marco/Documents/code.nosync/ai/linky && python3 -m pytest tests/test_study_mode.py -v -k "classify or concepts or cognitive or faq or build_study"`
- **Discipline:** tdd
- **Files:** scripts/linky/study.py, tests/test_study_mode.py
- **Tasks:**

### Task 5: Create study mode pipeline (truth anchoring + cognitive map + cross-analysis)

**Files:**
- Create: `scripts/linky/study.py`
- Test: `tests/test_study_mode.py` (extend)

- [ ] **Step 1: Write failing tests for study pipeline**

```python
# Append to tests/test_study_mode.py
from scripts.linky.study import (
    extract_concepts,
    generate_cognitive_map,
    classify_content_type,
    generate_faq,
    build_study_card_data,
)


def test_classify_content_type_github():
    assert classify_content_type("https://github.com/user/repo", {}) == "technical"


def test_classify_content_type_arxiv():
    assert classify_content_type("https://arxiv.org/abs/2401.00001", {}) == "academic"


def test_classify_content_type_medium():
    assert classify_content_type("https://medium.com/@user/post", {}) == "blog"


def test_extract_concepts_basic():
    markdown = """
# Redis Caching

Redis is an in-memory data store. It supports strings, hashes, lists, sets.
Use it for caching to reduce database load. TTL controls expiration.
"""
    concepts = extract_concepts(markdown)
    assert len(concepts) >= 2
    assert any("Redis" in c["name"] for c in concepts)


def test_extract_concepts_filters_structural_headings():
    markdown = """
# Introduction

This is just an intro paragraph.

# Redis Caching

Redis is an in-memory data store.

# Summary

This wraps up.
"""
    concepts = extract_concepts(markdown)
    names = [c["name"] for c in concepts]
    assert "Introduction" not in names
    assert "Summary" not in names
    assert "Redis Caching" in names


def test_generate_cognitive_map():
    concepts = [
        {"name": "Redis", "definition": "In-memory data store"},
        {"name": "Cache", "definition": "Temporary fast storage"},
        {"name": "TTL", "definition": "Time to live for cache entries"},
    ]
    mermaid = generate_cognitive_map(concepts)
    assert "graph" in mermaid
    assert "Redis" in mermaid


def test_build_study_card_data():
    extraction = {
        "url": "https://example.com/post",
        "markdown": "# Test Post\n\nRedis is a cache. TTL expires keys.",
        "metadata": {"title": "Test Post"},
    }
    card = build_study_card_data(extraction)
    assert card["title"] == "Test Post"
    assert card["source_url"] == "https://example.com/post"
    assert len(card["concepts"]) >= 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/marco/Documents/code.nosync/ai/linky && python3 -m pytest tests/test_study_mode.py -v`
Expected: FAIL — `study` module doesn't exist

- [ ] **Step 3: Create the study pipeline**

Create `scripts/linky/study.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/marco/Documents/code.nosync/ai/linky && python3 -m pytest tests/test_study_mode.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/marco/Documents/code.nosync/ai/linky
git add scripts/linky/study.py tests/test_study_mode.py
git commit -m "feat(study): add study mode pipeline (classify, extract, cognitive map, FAQ)"
```

---

### Phase 4: Integration — SKILL.md + E2E Test + Eval
- **Status:** complete
- **Verification command:** `cd /Users/marco/Documents/code.nosync/ai/linky && python3 -m pytest tests/ -v`
- **Discipline:** plain
- **Files:** SKILL.md, tests/test_study_mode.py, evals/study-evals.json
- **Tasks:**

### Task 6: Update SKILL.md with study mode trigger and workflow

**Files:**
- Modify: `SKILL.md`

- [ ] **Step 1: Add study mode trigger to description**

In the frontmatter `description:` field, append:

```
当用户表达"学习"、"深度阅读"、"做笔记"、"知识卡片"、"学习材料"、"study"等意图时，
linky 识别为 study 模式并路由到学习分析流水线，产出 Markdown 深度笔记 + 交互式 HTML 知识卡片。
```

- [ ] **Step 2: Add study mode workflow section**

Add a new section after the existing pipeline (after Step 8: Output adapter):

```markdown
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
```

- [ ] **Step 3: Commit**

```bash
cd /Users/marco/Documents/code.nosync/ai/linky
git add SKILL.md
git commit -m "feat(study): add study mode trigger, workflow, and comparison to SKILL.md"
```

---

### Task 7: Create Markdown knowledge card template

**Files:**
- Create: `references/study-card-template.md`

- [ ] **Step 1: Create the template**

Create `references/study-card-template.md` — the Markdown template that the AI agent uses
to structure each knowledge card. This is the Markdown output format referenced in
`references/output-styles/study.md`.

The template should include:
- Metadata header (source, type, date, verification stats)
- Overview section
- Core Concepts (with expandable details)
- Prerequisites
- Key Claims & Evidence (with truth anchoring tags)
- Code Examples (language-annotated)
- Cognitive Map (Mermaid code block)
- FAQ (5-8 items)
- Critical Assessment (strengths/weaknesses/gaps)
- Further Reading

- [ ] **Step 2: Commit**

```bash
cd /Users/marco/Documents/code.nosync/ai/linky
git add references/study-card-template.md
git commit -m "feat(study): add Markdown knowledge card template"
```

---

### Task 8: Integration test — end-to-end study mode

**Files:**
- Test: `tests/test_study_mode.py` (extend)

- [ ] **Step 1: Write integration test**

```python
# Append to tests/test_study_mode.py
from scripts.linky.html_card import render_html_card
from scripts.linky.study import build_study_card_data


def test_end_to_end_study_card():
    """Integration test: extraction result → study card data → HTML card."""
    extraction = {
        "url": "https://docs.python.org/3/library/asyncio.html",
        "markdown": (
            "# asyncio — Asynchronous I/O\n\n"
            "asyncio is a library for writing concurrent code.\n\n"
            "## Coroutines\n\n"
            "Coroutines declared with async/await syntax.\n\n"
            "## Event Loop\n\n"
            "The event loop is the core of asyncio.\n\n"
            "## Tasks\n\n"
            "Tasks are used to schedule coroutines concurrently."
        ),
        "metadata": {"title": "asyncio — Asynchronous I/O"},
    }

    card_data = build_study_card_data(extraction)

    assert card_data["title"] == "asyncio — Asynchronous I/O"
    assert card_data["source_url"] == "https://docs.python.org/3/library/asyncio.html"
    assert card_data["content_type"] == "technical"
    assert len(card_data["concepts"]) >= 2
    assert "graph" in card_data["cognitive_map"]
    assert len(card_data["faq"]) >= 3

    html = render_html_card(card_data)
    assert "<!DOCTYPE html>" in html
    assert "asyncio" in html
    assert "cdn" not in html.lower()
```

- [ ] **Step 2: Run full test suite**

Run: `cd /Users/marco/Documents/code.nosync/ai/linky && python3 -m pytest tests/test_study_mode.py tests/test_html_card.py -v`
Expected: ALL PASS

- [ ] **Step 3: Commit**

```bash
cd /Users/marco/Documents/code.nosync/ai/linky
git add tests/test_study_mode.py
git commit -m "feat(study): add end-to-end integration test for study mode"
```

---

### Task 9: skill-creator eval setup

**Files:**
- Create: `evals/study-evals.json` (in linky repo)
- Test: run eval prompts

- [ ] **Step 1: Create eval test cases**

Create `evals/study-evals.json`:

```json
{
  "skill_name": "linky-study",
  "evals": [
    {
      "id": 1,
      "prompt": "帮我学习这篇 asyncio 文档 https://docs.python.org/3/library/asyncio.html",
      "expected_output": "Markdown 深度笔记 + 交互式 HTML 知识卡片，包含认知地图和 FAQ",
      "files": []
    },
    {
      "id": 2,
      "prompt": "study these 3 links about Redis: https://redis.io/docs/latest/ https://redis.io/docs/latest/develop/ https://redis.io/docs/latest/operate/",
      "expected_output": "3 个独立知识卡片 + 交叉分析文档",
      "files": []
    },
    {
      "id": 3,
      "prompt": "深度阅读这篇论文 https://arxiv.org/abs/1706.03762 做学习笔记",
      "expected_output": "学术论文风格的知识卡片，包含方法论、发现、局限性分析",
      "files": []
    }
  ]
}
```

- [ ] **Step 2: Commit**

```bash
cd /Users/marco/Documents/code.nosync/ai/linky
git add evals/study-evals.json
git commit -m "feat(study): add eval test cases for study mode"
```

- [ ] **Step 3: Run first eval round with skill-creator**

Use skill-creator to run the eval prompts with the linky skill (which now includes study mode).
Follow skill-creator's Step 1 workflow: spawn all runs (with-skill AND baseline), draft assertions, capture timing, grade, aggregate, launch viewer.

---

## Errors Encountered
| Error | Attempt | Resolution |
|---|---|---|

## Decisions Log
| Date | Decision | Tier | Rationale |
|---|---|---|---|
| 2026-06-19 | linky 扩展模式（`--mode=study`）| Architecture | 用户选择：一个工具、一个触发点、全部基础设施复用 |
| 2026-06-19 | 内容提取使用 linky Python 脚本（scrapling_fetch.py）| Implementation | 用户选择：需要 JS 渲染和反爬虫能力 |
| 2026-06-19 | HTML 卡片内联 Mermaid.js（~1MB）| Implementation | P4 离线要求 |
| 2026-06-19 | 认知地图用 heading-based 概念提取 | Implementation | 简单启发式，后续可升级为 NLP |

## GSTACK REVIEW REPORT

### /autoplan Review — 2026-06-19

**Reviewer:** /cf:plan-review --depth=full (autoplan delegate)
**Plan:** study-skill — linky `--mode=study` extension
**Tasks:** 9 tasks across 4 phases

### Decisions Made: 10 total (8 auto-decided, 2 taste choices, 0 user challenges)

### Review Scores
- **CEO:** 4 findings (1 high, 2 medium, 1 low). Premises valid. Scope well-calibrated.
- **Design:** Skipped — no frontend UI scope (HTML template is generated artifact)
- **Eng:** 6 findings (2 high, 3 medium, 1 low). Architecture clean. Test gaps identified.
- **DX:** Skipped — linky skill extension, not standalone developer tool

### Critical Findings (must fix before /cf:execute)

**C1 + E5: study vs learning 区分不明确** (High)
linky 已有 `learning` output style（交互式学习判断：问用户问题），新 `study` style（知识卡片生成：被动消费）与之概念重叠。需要在 SKILL.md 中明确区分两者的目标和触发条件。

**E1: 代码/agent 数据流分裂** (High)
`build_study_card_data` 返回 `code_examples: []`, `claims: []`, `further_reading: []` — 这些字段完全由 AI agent 填充（通过 SKILL.md 指令），不是 Python 代码驱动。需要在 task_plan.md 中明确标注哪些字段由代码填充、哪些由 agent 填充。

**E2: extract_concepts 过于简单** (High)
heading-based 概念提取会把 "Introduction"、"Background"、"Summary" 等结构性标题误认为核心概念。需要添加过滤列表。

### Medium Findings (should fix)

**C2/E2:** 认知地图质量依赖概念提取质量。heading-based 启发式是 v1 的合理起点，但应记录为已知限制。

**C4:** 真理锚定在 v1 中完全依赖 AI agent 的 WebSearch 能力（不是 Python 代码）。这是设计选择，应在 task_plan.md 中明确记录。

**E3:** 缺少边缘情况测试（空内容、非 UTF-8、超长内容、畸形 HTML）。

**E4:** study mode 与 linky 现有 pipeline 的集成点不明确。应在 SKILL.md 中明确：study mode 在 classification 之后分叉。

### Low Findings

**C3:** Task 依赖关系隐含但未显式声明。
**E6:** Mermaid.js 内联 ~1MB，后续可优化。

### Auto-Decided: 8 decisions (see Decision Audit Trail above)

### Taste Choices

**T1:** 真理锚定实现方式 — agent-driven (WebSearch) vs code-driven (Python HTTP verification)。推荐 agent-driven（v1 简单），但 code-driven 更可靠。

**T2:** Mermaid.js 内联策略 — 完整版 (~1MB) vs CDN (违反离线原则) vs 精简子集。推荐完整版（P4 离线要求）。

### Decision Audit Trail

| # | Phase | Decision | Classification | Principle | Rationale |
|---|-------|----------|-----------|-----------|----------|
| 1 | CEO | Accept linky extension approach | Mechanical | P6 (bias toward action) | User's explicit choice |
| 2 | CEO | Accept scrapling_fetch.py dependency | Mechanical | P3 (pragmatic) | JS rendering needed |
| 3 | CEO | Accept no Mentor Mode in v1 | Mechanical | P3 (pragmatic) | Scope discipline |
| 4 | CEO | Accept offline HTML cards | Mechanical | P1 (completeness) | Learning materials need portability |
| 5 | CEO | Flag study vs learning overlap | Taste | P5 (explicit) | Conceptual confusion risk |
| 6 | Eng | Flag extract_concepts simplicity | Taste | P1 (completeness) | Real-world content has structural headings |
| 7 | Eng | Flag code/agent data flow split | Mechanical | P5 (explicit) | Mixed responsibility needs documentation |
| 8 | Eng | Accept heading-based extraction for v1 | Mechanical | P3 (pragmatic) | Simple heuristic, upgradeable later |

### Deferred to TODOS.md
- NLP-based concept extraction (post-v1)
- Mermaid.js minification / subset bundling (post-v1)
- Code-driven truth anchoring with web search API (post-v1)

### Next Step
Fix the 3 critical findings (C1+E5, E1, E2), then run `/cf:execute`.
