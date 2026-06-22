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


def test_render_claims_with_tags():
    """Claims render with correct tag CSS classes."""
    data = {
        "title": "Test", "source_url": "", "content_type": "", "date": "",
        "overview": "", "concepts": [], "cognitive_map": "", "faq": [],
        "code_examples": [], "further_reading": [],
        "claims": [
            {"claim": "Python is fast", "tag": "已验证", "evidence": "benchmarks"},
            {"claim": "X is dead", "tag": "存在争议", "evidence": "mixed signals"},
            {"claim": "Old API", "tag": "已过时", "evidence": "deprecated in v3"},
            {"claim": "New feature", "tag": "待确认", "evidence": "rumor"},
        ],
    }
    html = render_html_card(data)
    assert "tag-verified" in html
    assert "tag-disputed" in html
    assert "tag-outdated" in html
    assert "tag-pending" in html
    assert "Python is fast" in html


def test_render_code_examples():
    """Code examples render with language class and annotation."""
    data = {
        "title": "Test", "source_url": "", "content_type": "", "date": "",
        "overview": "", "concepts": [], "cognitive_map": "", "faq": [],
        "claims": [], "further_reading": [],
        "code_examples": [
            {"language": "python", "code": "print('hi')", "annotation": "simple output"},
        ],
    }
    html = render_html_card(data)
    assert "language-python" in html
    assert "print(&#x27;hi&#x27;)" in html
    assert "simple output" in html


def test_render_further_reading():
    """Further reading links render correctly."""
    data = {
        "title": "Test", "source_url": "", "content_type": "", "date": "",
        "overview": "", "concepts": [], "cognitive_map": "", "faq": [],
        "code_examples": [], "claims": [],
        "further_reading": [
            {"url": "https://example.com", "title": "Example Link"},
        ],
    }
    html = render_html_card(data)
    assert "https://example.com" in html
    assert "Example Link" in html


def test_render_html_card_empty_data():
    """Empty data produces valid HTML without errors."""
    html = render_html_card({})
    assert "<!DOCTYPE html>" in html
    assert "Untitled" in html  # default title


def test_render_xss_prevention():
    """User content is HTML-escaped to prevent XSS."""
    data = {
        "title": '<script>alert("xss")</script>',
        "source_url": "", "content_type": "", "date": "",
        "overview": "", "concepts": [], "cognitive_map": "", "faq": [],
        "code_examples": [], "claims": [], "further_reading": [],
    }
    html = render_html_card(data)
    # The escaped title should appear, not raw script tag in user content
    assert "&lt;script&gt;" in html
    # The title tag should contain escaped content
    assert "<h1>&lt;script&gt;" in html
