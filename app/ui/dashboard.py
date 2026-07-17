import streamlit as st

from app.data.filters import (
    filter_by_risk_levels,
    filter_af_specific,
    filter_by_keyword,
    sort_by_risk,
    summary_counts,
)
from app.ui.styles import (
    inject_base_styles,
    render_header_html,
    render_disclaimer_html,
    render_metric_tile_html,
    render_section_header_html,
    render_article_card_html,
    render_resources_section_html,
    HOW_TO_USE_TEXT,
)

_RISK_LEVELS = ["Critical", "High", "Medium", "Low"]


def _render_sidebar() -> tuple[set, bool, str, bool]:
    st.sidebar.markdown("**Filters**")
    selected = set()
    for level in _RISK_LEVELS:
        if st.sidebar.checkbox(level, value=True, key=f"filter_{level}"):
            selected.add(level)
    af_only = st.sidebar.checkbox("Air Force / Space Force specific only", value=False)
    query = st.sidebar.text_input("Search articles", value="")
    refresh_clicked = st.sidebar.button("Refresh now")
    return selected, af_only, query, refresh_clicked


def _render_summary_row(articles: list[dict]) -> None:
    counts = summary_counts(articles)
    cols = st.columns(4)
    for col, level in zip(cols, _RISK_LEVELS):
        with col:
            st.markdown(render_metric_tile_html(level, counts[level], level), unsafe_allow_html=True)


def _render_feed_section(title: str, articles: list[dict], empty_message: str) -> None:
    st.markdown(render_section_header_html(title), unsafe_allow_html=True)
    if not articles:
        st.info(empty_message)
        return
    visible, rest = articles[:20], articles[20:]
    for article in visible:
        st.markdown(render_article_card_html(article), unsafe_allow_html=True)
    if rest:
        with st.expander(f"Show {len(rest)} more articles"):
            for article in rest:
                st.markdown(render_article_card_html(article), unsafe_allow_html=True)


def _render_resources_section() -> None:
    st.markdown(render_section_header_html("Resources"), unsafe_allow_html=True)
    st.markdown(render_resources_section_html(), unsafe_allow_html=True)


def render_dashboard(articles: list[dict], key_missing: bool, last_refreshed: str) -> bool:
    inject_base_styles()
    st.markdown(render_header_html(), unsafe_allow_html=True)
    st.markdown(render_disclaimer_html(), unsafe_allow_html=True)

    with st.expander("How to Use This Site"):
        st.markdown(HOW_TO_USE_TEXT)

    if key_missing:
        st.info("Add ANTHROPIC_API_KEY to your secrets to enable risk assessment.")

    selected_levels, af_only, query, refresh_clicked = _render_sidebar()
    st.sidebar.caption(f"Last refreshed: {last_refreshed}")

    if not articles:
        st.warning("No housing-related coverage found in the last 48 hours.")
        _render_resources_section()
        return refresh_clicked

    filtered = filter_by_risk_levels(articles, selected_levels)
    filtered = filter_by_keyword(filtered, query)
    if af_only:
        filtered = filter_af_specific(filtered)

    _render_summary_row(filtered)

    main_feed = sort_by_risk(filtered)
    _render_feed_section(
        "Housing Coverage Feed", main_feed, "No articles match the current filters."
    )

    af_feed = sort_by_risk(filter_af_specific(filtered))
    _render_feed_section(
        "Air Force / Space Force Specific",
        af_feed,
        "No Air Force/Space Force-specific stories in the last 48 hours. Check back soon.",
    )

    _render_resources_section()

    return refresh_clicked
