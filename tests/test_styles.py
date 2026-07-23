from datetime import datetime, timezone, timedelta

from app.ui import styles


def test_risk_colors_known_level():
    colors = styles.risk_colors("Critical")
    assert colors["stripe"] == "#C0392B"


def test_risk_colors_unknown_level_returns_fallback():
    colors = styles.risk_colors(None)
    assert colors["stripe"] == styles._UNKNOWN_COLOR["stripe"]


def test_how_to_use_text_covers_risk_levels_and_filters():
    for term in ("Critical", "High", "Medium", "Low", "Refresh now", "Air Force / Space Force"):
        assert term in styles.HOW_TO_USE_TEXT


def test_render_weekly_summary_html_contains_escaped_text_and_no_newlines():
    html_out = styles.render_weekly_summary_html("Two stories this week.\nOne is <Critical>.")
    assert "Two stories this week." in html_out
    assert "&lt;Critical&gt;" in html_out
    assert "<Critical>" not in html_out
    assert "\n" not in html_out


def test_render_header_html_contains_title_and_logo():
    html = styles.render_header_html()
    assert styles.APP_TITLE in html
    assert styles.SECONDARY_COLOR in html
    assert "data:image/png;base64," in html


def test_logo_data_uri_is_cached_and_valid_base64():
    import base64

    uri = styles._logo_data_uri()
    assert uri.startswith("data:image/png;base64,")
    encoded = uri.split(",", 1)[1]
    # Should decode without error and match the actual file on disk.
    decoded = base64.b64decode(encoded)
    assert decoded == styles._LOGO_PATH.read_bytes()
    assert styles._logo_data_uri() is uri  # second call returns the cached string


def test_render_resources_section_html_lists_all_orgs():
    html = styles.render_resources_section_html(["Military.com", "AF.mil"])
    for link in styles.RESOURCE_LINKS:
        assert link["name"] in html
        assert link["url"] in html
        assert link["description"] in html


def test_render_resources_section_html_lists_source_names():
    html = styles.render_resources_section_html(["Military.com", "Stars and Stripes", "AF.mil"])
    assert "Military.com" in html
    assert "Stars and Stripes" in html
    assert "AF.mil" in html
    assert "News sources monitored" in html


def test_render_resources_section_html_has_no_embedded_newlines():
    # A blank/whitespace-only line inside an st.markdown(unsafe_allow_html=True)
    # call makes Streamlit render everything after it as a literal code block
    # instead of HTML. Guard against that regressing.
    assert "\n" not in styles.render_resources_section_html(["Military.com"])


def test_render_article_card_html_has_no_embedded_newlines_with_empty_summary_and_rationale():
    article = {
        "title": "Routine housing announcement",
        "summary": "",
        "risk_level": None,
        "risk_rationale": "",
        "source": "Military.com",
        "url": "http://example.com/b",
        "published_at": "",
    }
    assert "\n" not in styles.render_article_card_html(article)


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


def test_render_article_card_html_escapes_script_tag_in_title():
    article = {
        "title": "Breaking <script>alert(1)</script> news",
        "summary": "",
        "risk_level": "Critical",
        "risk_rationale": "",
        "source": "Example News",
        "url": "http://example.com/c",
        "published_at": "",
    }
    html_output = styles.render_article_card_html(article)
    assert "<script>" not in html_output
    assert "&lt;script&gt;" in html_output


def test_time_ago_hours():
    published = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
    assert styles.time_ago(published) == "3h ago"


def test_time_ago_minutes():
    published = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
    assert styles.time_ago(published) == "15m ago"


def test_time_ago_empty_input_returns_empty_string():
    assert styles.time_ago("") == ""
