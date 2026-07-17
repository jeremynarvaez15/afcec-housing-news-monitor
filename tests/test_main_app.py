import streamlit as st
from streamlit.testing.v1 import AppTest

_FAKE_ARTICLE = {
    "title": "Barracks mold exposure sickens airmen",
    "description": "desc",
    "url": "http://example.com/a",
    "source": "Test Source",
    "published_at": "2026-07-16T00:00:00+00:00",
}

_FAKE_ASSESSED = {
    **_FAKE_ARTICLE,
    "summary": "Summary text.",
    "risk_level": "Critical",
    "risk_rationale": "safety hazard",
    "af_specific": True,
}


def _patch_data_layer(monkeypatch, api_key=""):
    import app.data.news_fetcher as news_fetcher
    import app.data.risk_assessor as risk_assessor

    monkeypatch.setattr(news_fetcher, "fetch_housing_articles", lambda: [_FAKE_ARTICLE])
    monkeypatch.setattr(risk_assessor, "assess_risk", lambda articles, api_key: [_FAKE_ASSESSED])
    # Force st.secrets to a known value regardless of any local secrets.toml,
    # so these tests are deterministic on every machine. main.py checks
    # load_if_toml_exists() before calling get() (to avoid the st.error banner
    # Streamlit prints when no secrets.toml exists anywhere on disk), so both
    # need patching to simulate a machine that does/doesn't have a secret set.
    monkeypatch.setattr(st.secrets, "load_if_toml_exists", lambda: bool(api_key))
    monkeypatch.setattr(st.secrets, "get", lambda key, default=None: api_key or default)
    # main.py's cache key is (cache_buster,), which is the same within any given
    # hour across test runs — clear it so one test's fake data can't leak into another.
    st.cache_data.clear()


def test_app_runs_without_exceptions(monkeypatch):
    _patch_data_layer(monkeypatch, api_key="fake-key")

    at = AppTest.from_file("main.py")
    at.run()

    assert not at.exception


def test_app_shows_key_missing_message_when_no_secret(monkeypatch):
    _patch_data_layer(monkeypatch, api_key="")

    at = AppTest.from_file("main.py")
    at.run()

    info_texts = [i.value for i in at.info]
    assert any("ANTHROPIC_API_KEY" in t for t in info_texts)


def test_app_hides_key_missing_message_when_secret_present(monkeypatch):
    _patch_data_layer(monkeypatch, api_key="fake-key")

    at = AppTest.from_file("main.py")
    at.run()

    info_texts = [i.value for i in at.info]
    assert not any("ANTHROPIC_API_KEY" in t for t in info_texts)
