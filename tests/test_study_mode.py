from scripts.linky.report import normalize_output_style, STUDY_OUTPUT_STYLE
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
