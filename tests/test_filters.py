from app.data.filters import (
    filter_by_risk_levels,
    filter_af_specific,
    filter_by_keyword,
    sort_by_risk,
    summary_counts,
)


def _article(**overrides):
    base = {
        "title": "Test article",
        "summary": "Test summary",
        "risk_level": "Medium",
        "af_specific": False,
        "url": "http://example.com",
    }
    base.update(overrides)
    return base


def test_filter_by_risk_levels_keeps_only_selected_levels():
    articles = [_article(risk_level="Critical"), _article(risk_level="Low")]
    result = filter_by_risk_levels(articles, {"Critical"})
    assert len(result) == 1
    assert result[0]["risk_level"] == "Critical"


def test_filter_by_risk_levels_always_keeps_unrated_articles():
    # An article with risk_level=None (missing API key, or a failed AI call)
    # has no level to filter by, so it must never be silently dropped just
    # because the sidebar's Critical/High/Medium/Low checkboxes don't list "None".
    articles = [_article(risk_level=None), _article(risk_level="Low")]
    result = filter_by_risk_levels(articles, {"Critical"})
    assert len(result) == 1
    assert result[0]["risk_level"] is None


def test_filter_af_specific_keeps_only_af_specific_true():
    articles = [_article(af_specific=True), _article(af_specific=False)]
    result = filter_af_specific(articles)
    assert len(result) == 1
    assert result[0]["af_specific"] is True


def test_filter_by_keyword_matches_title_case_insensitive():
    articles = [
        _article(title="Mold found in barracks"),
        _article(title="Ribbon cutting ceremony"),
    ]
    result = filter_by_keyword(articles, "MOLD")
    assert len(result) == 1
    assert "Mold" in result[0]["title"]


def test_filter_by_keyword_empty_query_returns_all():
    articles = [_article(), _article()]
    result = filter_by_keyword(articles, "")
    assert len(result) == 2


def test_sort_by_risk_orders_critical_first():
    articles = [_article(risk_level="Low"), _article(risk_level="Critical"), _article(risk_level="Medium")]
    result = sort_by_risk(articles)
    assert [a["risk_level"] for a in result] == ["Critical", "Medium", "Low"]


def test_sort_by_risk_puts_unrated_last():
    articles = [_article(risk_level=None), _article(risk_level="High")]
    result = sort_by_risk(articles)
    assert result[0]["risk_level"] == "High"
    assert result[1]["risk_level"] is None


def test_summary_counts_tallies_each_level():
    articles = [_article(risk_level="Critical"), _article(risk_level="Critical"), _article(risk_level="Low")]
    counts = summary_counts(articles)
    assert counts == {"Critical": 2, "High": 0, "Medium": 0, "Low": 1}
