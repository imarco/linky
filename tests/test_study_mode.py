from scripts.linky.report import normalize_output_style, STUDY_OUTPUT_STYLE
from scripts.linky.html_card import render_html_card
from scripts.linky.study import (
    extract_concepts,
    generate_cognitive_map,
    classify_content_type,
    generate_faq,
    build_study_card_data,
)


def test_study_style_constant():
    assert STUDY_OUTPUT_STYLE == "study"


def test_normalize_study_aliases():
    assert normalize_output_style("study") == "study"
    assert normalize_output_style("学习卡片") == "study"
    assert normalize_output_style("知识卡片") == "study"
    assert normalize_output_style("study-card") == "study"


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
    assert len(concepts) >= 1
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
    assert card_data["content_type"] == "tutorial"
    assert len(card_data["concepts"]) >= 2
    assert "graph" in card_data["cognitive_map"]
    assert len(card_data["faq"]) >= 3

    html = render_html_card(card_data)
    assert "<!DOCTYPE html>" in html
    assert "asyncio" in html
    assert "cdn" not in html.lower()
