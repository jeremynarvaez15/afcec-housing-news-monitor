from types import SimpleNamespace
from datetime import datetime, timezone, timedelta

import app.data.news_fetcher as news_fetcher
from app.data.news_fetcher import (
    fetch_housing_articles,
    fetch_feed_diagnostics,
    get_source_names,
    _matches_keywords,
    _name_matches,
    _FEEDS,
)


def _struct_time(hours_ago):
    dt = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    return dt.timetuple()


def _entry(title="", summary="", link="", hours_ago=1):
    return SimpleNamespace(
        title=title, summary=summary, link=link,
        published_parsed=_struct_time(hours_ago),
    )


def test_matches_keywords_topic_term():
    assert _matches_keywords("MHPI program under review", "") is True


def test_matches_keywords_partner_name():
    assert _matches_keywords(
        "Local news roundup", "Hunt Military Communities announced repairs"
    ) is True


def test_matches_keywords_unrelated_story_returns_false():
    assert _matches_keywords("Local football team wins championship", "") is False


def test_matches_keywords_quality_of_life_term():
    assert _matches_keywords("Base leaders address quality of life concerns", "") is True


def test_matches_keywords_installation_housing_term():
    assert _matches_keywords("Installation housing inspections underway", "") is True


def test_matches_keywords_advocacy_org_name():
    assert _matches_keywords(
        "Advocates weigh in", "Project On Government Oversight released a new report"
    ) is True


def test_name_matches_rejects_short_ambiguous_name():
    assert _name_matches("JL", "jl properties announced today") is False


def test_fetch_housing_articles_filters_by_keyword_and_recency(monkeypatch):
    entries = [
        _entry(title="MHPI review at base", summary="details", link="http://a", hours_ago=1),
        _entry(title="Local team wins game", summary="details", link="http://b", hours_ago=1),
        _entry(title="Barracks mold found", summary="details", link="http://c", hours_ago=200),
    ]
    fake_parsed = SimpleNamespace(entries=entries)
    monkeypatch.setattr(news_fetcher.feedparser, "parse", lambda url: fake_parsed)

    articles = fetch_housing_articles()

    urls = {a["url"] for a in articles}
    assert "http://a" in urls
    assert "http://b" not in urls
    assert "http://c" not in urls


def test_fetch_housing_articles_dedupes_by_url(monkeypatch):
    entries = [_entry(title="MHPI update", summary="", link="http://dup", hours_ago=1)]
    fake_parsed = SimpleNamespace(entries=entries)
    monkeypatch.setattr(news_fetcher.feedparser, "parse", lambda url: fake_parsed)

    articles = fetch_housing_articles()

    urls = [a["url"] for a in articles]
    assert urls.count("http://dup") == 1


def test_fetch_housing_articles_skips_feed_that_raises(monkeypatch):
    def _raise(url):
        raise ConnectionError("feed unavailable")

    monkeypatch.setattr(news_fetcher.feedparser, "parse", _raise)

    articles = fetch_housing_articles()

    assert articles == []


def test_fetch_feed_diagnostics_reports_entry_count_per_feed(monkeypatch):
    entries = [_entry(title="Some story", summary="", link="http://x", hours_ago=1)]
    fake_parsed = SimpleNamespace(entries=entries, bozo=False, bozo_exception=None, status=200)
    monkeypatch.setattr(news_fetcher.feedparser, "parse", lambda url: fake_parsed)

    diagnostics = fetch_feed_diagnostics()

    assert len(diagnostics) == len(_FEEDS)
    for d in diagnostics:
        assert d["entry_count"] == 1
        assert d["error"] is None
        assert d["http_status"] == 200


def test_fetch_feed_diagnostics_reports_error_when_parse_raises(monkeypatch):
    def _raise(url):
        raise ConnectionError("feed unavailable")

    monkeypatch.setattr(news_fetcher.feedparser, "parse", _raise)

    diagnostics = fetch_feed_diagnostics()

    assert len(diagnostics) == len(_FEEDS)
    for d in diagnostics:
        assert d["entry_count"] == 0
        assert "feed unavailable" in d["error"]


def test_fetch_feed_diagnostics_reports_bozo_parse_errors(monkeypatch):
    fake_parsed = SimpleNamespace(
        entries=[], bozo=True, bozo_exception=ValueError("malformed xml"), status=200
    )
    monkeypatch.setattr(news_fetcher.feedparser, "parse", lambda url: fake_parsed)

    diagnostics = fetch_feed_diagnostics()

    assert len(diagnostics) == len(_FEEDS)
    for d in diagnostics:
        assert d["entry_count"] == 0
        assert "malformed xml" in d["error"]


def test_get_source_names_returns_unique_names_in_feed_order():
    names = get_source_names()

    # Stars and Stripes has two feed entries in _FEEDS; the display list must
    # not show it twice.
    assert names.count("Stars and Stripes") == 1
    assert len(names) == len(set(names))
    assert "Military.com" in names
    assert "AF.mil" in names
    # Order should match first appearance in _FEEDS, not be alphabetized —
    # keeps it stable and predictable rather than surprising on re-sort.
    assert names[0] == "Military.com"
