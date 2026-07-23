import base64
import html
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

# JLL brand palette: Rainbow Red primary, black secondary.
PRIMARY_COLOR = "#E30613"
SECONDARY_COLOR = "#000000"
SILVER = "#C0C0C0"
BG = "#F5F6F8"

_LOGO_PATH = Path(__file__).parent / "assets" / "jll_logo.png"
_logo_data_uri_cache: str | None = None


def _logo_data_uri() -> str:
    global _logo_data_uri_cache
    if _logo_data_uri_cache is None:
        encoded = base64.b64encode(_LOGO_PATH.read_bytes()).decode("ascii")
        _logo_data_uri_cache = f"data:image/png;base64,{encoded}"
    return _logo_data_uri_cache

APP_TITLE = "Media Monitoring for Air Force Housing"
DISCLAIMER_TEXT = (
    "This is an unofficial personal tool for media monitoring and risk management, "
    "not an official Department of the Air Force system."
)

RISK_COLORS = {
    "Critical": {"stripe": "#C0392B", "bg": "#FBEAEA", "text": "#922B21"},
    "High": {"stripe": "#E67E22", "bg": "#FDF0E4", "text": "#A85D18"},
    "Medium": {"stripe": "#D4AC0D", "bg": "#FBF3D9", "text": "#8A6D0B"},
    "Low": {"stripe": "#7F8C8D", "bg": "#EEF0F0", "text": "#5F6A6A"},
}
_UNKNOWN_COLOR = {"stripe": "#B0B0B0", "bg": "#F0F0F0", "text": "#707070"}

_RISK_ICON = {"Critical": "⚠", "High": "⚠", "Medium": "●", "Low": "●"}

HOW_TO_USE_TEXT = """\
**What this is:** This tool scans military/defense and general news for coverage of \
MHPI, privatized housing, dorms, barracks, and DoD-owned housing from the last 2 weeks, \
summarizes each article with AI, and flags its reputational/operational risk to the \
Air Force. Housing-specific coverage is infrequent — expect a quiet week to mean \
little happened, not that the tool is broken.

**Risk levels:**
- 🔴 **Critical** — safety incidents, deaths, criminal charges, active investigations
- 🟠 **High** — health/safety hazard exposés, lawsuits, GAO reports, systemic problems
- 🟡 **Medium** — tenant complaints, contractor disputes, funding/policy news
- ⚪ **Low** — routine announcements, minor coverage

**Using the filters (left sidebar):**
- Check or uncheck risk levels to show only what you care about
- "Air Force / Space Force specific only" narrows the feed to AF/SSF-specific stories
- Use the search box to find articles by keyword
- Click "Refresh now" to check for new articles immediately — otherwise the feed \
refreshes automatically about once an hour

**Resources:** The collapsible Resources section lists every news source this tool \
monitors, plus links to independent advocacy and watchdog organizations for further \
reading.

**A note on AI risk levels:** These are AI-generated starting points, not official \
determinations — always apply your own judgment before acting on them.
"""

RESOURCE_LINKS = [
    {
        "name": "Change the Air Foundation",
        "url": "https://changetheairfoundation.org",
        "description": "Indoor air quality advocacy, including a dedicated mold-in-military-housing focus",
    },
    {
        "name": "Project On Government Oversight (POGO)",
        "url": "https://www.pogo.org",
        "description": "Independent government watchdog covering defense oversight and accountability",
    },
    {
        "name": "National Military Family Association",
        "url": "https://www.militaryfamily.org",
        "description": "Advocacy for military families, including housing and quality-of-life issues",
    },
]


def risk_colors(risk_level: str | None) -> dict:
    return RISK_COLORS.get(risk_level, _UNKNOWN_COLOR)


def time_ago(published_at: str) -> str:
    if not published_at:
        return ""
    try:
        dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        hours = int(delta.total_seconds() // 3600)
        minutes = int((delta.total_seconds() % 3600) // 60)
        if hours >= 1:
            return f"{hours}h ago"
        return f"{minutes}m ago"
    except Exception:
        return ""


def inject_base_styles() -> None:
    st.markdown(
        f"""
        <style>
        .afhn-card {{
            border-radius: 10px; overflow: hidden;
            box-shadow: 0 1px 5px rgba(0,0,0,0.09);
            background: #FFFFFF; margin-bottom: 12px; display: flex;
        }}
        .afhn-card-stripe {{ width: 4px; flex-shrink: 0; }}
        .afhn-card-body {{ padding: 12px 14px; flex: 1; }}
        .afhn-badge {{
            font-size: 11px; font-weight: 600; padding: 2px 9px;
            border-radius: 10px; display: inline-block; margin-right: 8px;
        }}
        .afhn-section-header {{ font-size: 16px; font-weight: 700; color: #2C2C2A; margin-bottom: 4px; }}
        .afhn-section-underline {{
            width: 48px; height: 3px; background: {PRIMARY_COLOR};
            border-radius: 2px; margin-bottom: 14px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# Streamlit's markdown renderer treats a blank (or whitespace-only) line inside
# an HTML block as the end of that block, dumping any indented content that
# follows into a literal code block instead of rendering it. Every function
# below therefore returns HTML as a single line with no embedded newlines,
# even where a conditional fragment might otherwise be empty.


def render_header_html() -> str:
    return (
        f'<div style="background:{SECONDARY_COLOR};color:#FFFFFF;'
        f'padding:16px 24px;border-radius:10px;display:flex;align-items:center;gap:16px;">'
        f'<img src="{_logo_data_uri()}" alt="JLL" style="height:38px;width:auto;display:block;flex-shrink:0;">'
        f'<div style="font-size:19px;font-weight:600;">{APP_TITLE}</div>'
        f'</div>'
    )


def render_disclaimer_html() -> str:
    return (
        f'<div style="background:{BG};border-bottom:1px solid {SILVER};padding:8px 24px;'
        f'font-size:12px;color:#5F5E5A;font-style:italic;border-radius:0 0 10px 10px;">'
        f'{DISCLAIMER_TEXT}'
        f'</div>'
    )


def render_metric_tile_html(label: str, count: int, risk_level: str) -> str:
    colors = risk_colors(risk_level)
    return (
        f'<div style="background:#FFFFFF;border-radius:8px;box-shadow:0 1px 4px rgba(0,0,0,0.08);'
        f'display:flex;overflow:hidden;">'
        f'<div style="width:4px;background:{colors["stripe"]};"></div>'
        f'<div style="padding:10px 12px;">'
        f'<div style="font-size:12px;color:#888780;">{label}</div>'
        f'<div style="font-size:22px;font-weight:600;color:#2C2C2A;">{count}</div>'
        f'</div>'
        f'</div>'
    )


def render_section_header_html(label: str) -> str:
    return (
        f'<div class="afhn-section-header">{label}</div>'
        f'<div class="afhn-section-underline"></div>'
    )


def _clean_narrative(text: str) -> str:
    # Strip newlines before escaping — AI-generated text isn't guaranteed to be
    # single-line, and an embedded newline here would trigger the same
    # blank-line-breaks-the-HTML-block issue documented above.
    return html.escape((text or "").replace("\n", " ").strip())


def render_weekly_summary_html(total: int, counts: dict, narrative: dict) -> str:
    """Counts (total + per-tier) come from our own code (summary_counts() in
    filters.py, plus len(articles)) — never from the AI, which shouldn't be
    trusted to count reliably. narrative supplies the qualitative one-liner
    per tier from generate_weekly_summary(), which may be empty per tier."""
    def bullet(label: str, count: int, text: str) -> str:
        clean = _clean_narrative(text)
        suffix = f": {clean}" if clean else ""
        return f'<li><strong>{label}</strong> ({count}){suffix}</li>'

    items = (
        f'<li><strong>Total stories identified:</strong> {total}</li>'
        + bullet("Critical", counts.get("Critical", 0), narrative.get("critical_summary", ""))
        + bullet("High", counts.get("High", 0), narrative.get("high_summary", ""))
        + bullet("Medium", counts.get("Medium", 0), narrative.get("medium_summary", ""))
    )
    return (
        f'<div class="afhn-card" style="display:block;padding:14px 18px;">'
        f'<div style="font-size:13px;font-weight:600;color:#2C2C2A;margin-bottom:6px;">Coverage summary</div>'
        f'<ul style="margin:0;padding-left:18px;font-size:14px;color:#333333;line-height:1.7;">{items}</ul>'
        f'</div>'
    )


def render_resources_section_html(source_names: list[str]) -> str:
    sources_html = ", ".join(html.escape(name) for name in source_names)
    links_html = "".join(
        f'<div style="padding:10px 0;border-bottom:1px solid {SILVER};">'
        f'<a href="{html.escape(link["url"], quote=True)}" '
        f'style="font-size:14px;font-weight:600;color:{PRIMARY_COLOR};">{html.escape(link["name"])}</a>'
        f'<div style="font-size:12px;color:#5F5E5A;margin-top:2px;">{html.escape(link["description"])}</div>'
        f'</div>'
        for link in RESOURCE_LINKS
    )
    return (
        f'<div class="afhn-card" style="display:block;padding:14px 18px;">'
        f'<div style="font-size:13px;font-weight:600;color:#2C2C2A;margin-bottom:6px;">News sources monitored</div>'
        f'<div style="font-size:12px;color:#5F5E5A;padding-bottom:12px;border-bottom:1px solid {SILVER};">{sources_html}</div>'
        f'<div style="font-size:13px;font-weight:600;color:#2C2C2A;margin-top:12px;">Advocacy &amp; watchdog organizations</div>'
        f'{links_html}'
        f'</div>'
    )


def render_article_card_html(article: dict) -> str:
    risk_level = article.get("risk_level")
    colors = risk_colors(risk_level)
    badge_label = risk_level or "Unrated"
    icon = _RISK_ICON.get(risk_level, "?")
    title = html.escape(article.get("title", ""))
    summary = html.escape(article.get("summary") or "")
    rationale = html.escape(article.get("risk_rationale") or "")
    source = html.escape(article.get("source", ""))
    url = html.escape(article.get("url", "#"), quote=True)
    ago = time_ago(article.get("published_at", ""))
    meta = " &middot; ".join(filter(None, [source, ago]))

    summary_html = (
        f'<div style="font-size:13px;color:#5F5E5A;margin-bottom:4px;">{summary}</div>'
        if summary else ""
    )
    rationale_html = (
        f'<div style="font-size:12px;color:#888780;margin-bottom:4px;">Risk Rationale: {rationale}</div>'
        if rationale else ""
    )

    return (
        f'<div class="afhn-card">'
        f'<div class="afhn-card-stripe" style="background:{colors["stripe"]};"></div>'
        f'<div class="afhn-card-body">'
        f'<div style="margin-bottom:4px;">'
        f'<span class="afhn-badge" style="background:{colors["bg"]};color:{colors["text"]};">{icon} {badge_label}</span>'
        f'<span style="font-size:14px;font-weight:600;color:#2C2C2A;">{title}</span>'
        f'</div>'
        f'{summary_html}'
        f'{rationale_html}'
        f'<div style="font-size:12px;color:#888780;">{meta} &middot; <a href="{url}" style="color:{PRIMARY_COLOR};">Read full article</a></div>'
        f'</div>'
        f'</div>'
    )
