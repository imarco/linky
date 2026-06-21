from scripts.linky.report import normalize_output_style, STUDY_OUTPUT_STYLE


def test_study_style_constant():
    assert STUDY_OUTPUT_STYLE == "study"


def test_normalize_study_aliases():
    assert normalize_output_style("study") == "study"
    assert normalize_output_style("学习卡片") == "study"
    assert normalize_output_style("知识卡片") == "study"
    assert normalize_output_style("study-card") == "study"
