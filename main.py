import time

import streamlit as st

from app.data.news_fetcher import fetch_housing_articles, fetch_feed_diagnostics, get_source_names
from app.data.risk_assessor import assess_risk
from app.ui.dashboard import render_dashboard

st.set_page_config(
    page_title="Media Monitoring for Air Force Housing",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

_REFRESH_INTERVAL = 3600


def _get_api_key() -> str:
    # st.secrets.get()/__getitem__ prints a visible st.error banner (and then
    # raises FileNotFoundError) when no secrets.toml exists anywhere on disk,
    # which is the normal state for a fresh checkout that hasn't configured
    # secrets yet. load_if_toml_exists() checks for the file without that
    # side effect, so we only touch .get() once we know it's safe to do so.
    if not st.secrets.load_if_toml_exists():
        return ""
    return st.secrets.get("ANTHROPIC_API_KEY", "")


@st.cache_data(ttl=_REFRESH_INTERVAL)
def load_housing_news(_cache_buster: int):
    anthropic_key = _get_api_key()
    articles = fetch_housing_articles()
    return assess_risk(articles, anthropic_key)


anthropic_key = _get_api_key()
cache_buster = int(time.time() // _REFRESH_INTERVAL)

with st.spinner("Loading housing news coverage..."):
    articles = load_housing_news(cache_buster)

feed_diagnostics = None
if not articles:
    # Only re-fetch for diagnostics when there's actually nothing to show —
    # this is troubleshooting info, not part of the normal render path.
    feed_diagnostics = fetch_feed_diagnostics()

last_refreshed = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
refresh_clicked = render_dashboard(
    articles,
    key_missing=(not anthropic_key),
    last_refreshed=last_refreshed,
    source_names=get_source_names(),
    feed_diagnostics=feed_diagnostics,
)

if refresh_clicked:
    load_housing_news.clear()
    st.rerun()
