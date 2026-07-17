from datetime import datetime, timezone, timedelta

from app.ui import styles


def test_risk_colors_known_level():
    colors = styles.risk_colors("Critical")
    assert colors["stripe"] == "#C0392B"


def test_risk_colors_unknown_level_returns_fallback():
    colors = styles.risk_colors(None)
    assert colors["stripe"] == styles._UNKNOWN_COLOR["stripe"]


def test_render_header_html_contains_title_and_color():
    html = styles.render_header_html()
    assert styles.APP_TITLE in html
    assert styles.AF_BLUE in html


def test_render_disclaimer_html_contains_disclaimer_text():
    html = styles.render_disclaimer_html()
    assert styles.DISCLAIMER_TEXT in html


def test_render_metric_tile_html_contains_label_and_count():
    html = styles.render_metric_tile_html("Critical", 4, "Critical")
    assert "Critical" in html
    assert "4" in html
    assert styles.RISK_COLORS["Critical"]["stripe"] in html


def test_render_section_header_html_contains_label():
    html = styles.render_section_header_html("Housing Coverage Feed")
    assert "Housing Coverage Feed" in html


def test_render_article_card_html_contains_title_summary_and_badge():
    article = {
        "title": "Barracks mold exposure sickens airmen",
        "summary": "Investigation launched.",
        "risk_level": "Critical",
        "risk_rationale": "health/safety hazard",
        "source": "Stars and Stripes",
        "url": "http://example.com/a",
        "published_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
    }
    html = styles.render_article_card_html(article)
    assert "Barracks mold exposure sickens airmen" in html
    assert "Investigation launched." in html
    assert "Critical" in html
    assert "health/safety hazard" in html
    assert "Stars and Stripes" in html
    assert "2h ago" in html
    assert "http://example.com/a" in html


def test_render_article_card_html_handles_missing_risk_level():
    article = {
        "title": "Routine housing announcement",
        "summary": "",
        "risk_level": None,
        "risk_rationale": "",
        "source": "Military.com",
        "url": "http://example.com/b",
        "published_at": "",
    }
    html = styles.render_article_card_html(article)
    assert "Unrated" in html
    assert styles._UNKNOWN_COLOR["stripe"] in html


def test_time_ago_hours():
    published = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
    assert styles.time_ago(published) == "3h ago"


def test_time_ago_minutes():
    published = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
    assert styles.time_ago(published) == "15m ago"


def test_time_ago_empty_input_returns_empty_string():
    assert styles.time_ago("") == ""
