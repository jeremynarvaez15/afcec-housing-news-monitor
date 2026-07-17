from types import SimpleNamespace
from datetime import datetime, timezone, timedelta

import app.data.news_fetcher as news_fetcher
from app.data.news_fetcher import fetch_housing_articles, _matches_keywords, _name_matches


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
        _entry(title="Barracks mold found", summary="details", link="http://c", hours_ago=100),
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
