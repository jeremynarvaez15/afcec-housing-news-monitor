import html
from datetime import datetime, timezone

import streamlit as st

AF_BLUE = "#00308F"
AF_BLUE_DARK = "#002266"
SILVER = "#C0C0C0"
BG = "#F5F6F8"

APP_TITLE = "Media Monitoring for Air Force Housing"
DISCLAIMER_TEXT = (
    "This is an unofficial personal risk management tool, "
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
MHPI, privatized housing, dorms, barracks, and DoD-owned housing, summarizes each \
article with AI, and flags its reputational/operational risk to the Air Force.

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

**Resources:** Links at the bottom of the page point to independent advocacy and \
watchdog organizations for further reading.

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
            width: 48px; height: 3px; background: {AF_BLUE};
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
        f'<div style="background:linear-gradient(135deg,{AF_BLUE},{AF_BLUE_DARK});color:#FFFFFF;'
        f'padding:20px 24px;border-radius:10px;display:flex;align-items:center;gap:14px;">'
        f'<div style="width:42px;height:42px;border-radius:50%;background:rgba(255,255,255,0.14);'
        f'display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:22px;">&#127968;</div>'
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


def render_resources_section_html() -> str:
    links_html = "".join(
        f'<div style="padding:10px 0;border-bottom:1px solid {SILVER};">'
        f'<a href="{html.escape(link["url"], quote=True)}" '
        f'style="font-size:14px;font-weight:600;color:{AF_BLUE};">{html.escape(link["name"])}</a>'
        f'<div style="font-size:12px;color:#5F5E5A;margin-top:2px;">{html.escape(link["description"])}</div>'
        f'</div>'
        for link in RESOURCE_LINKS
    )
    return f'<div class="afhn-card" style="display:block;padding:14px 18px;">{links_html}</div>'


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
        f'<div style="font-size:12px;color:#888780;margin-bottom:4px;">Why: {rationale}</div>'
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
        f'<div style="font-size:12px;color:#888780;">{meta} &middot; <a href="{url}" style="color:{AF_BLUE};">Read full article</a></div>'
        f'</div>'
        f'</div>'
    )
