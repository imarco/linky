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
