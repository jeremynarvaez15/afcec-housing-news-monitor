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


def render_header_html() -> str:
    return f"""
    <div style="background:linear-gradient(135deg,{AF_BLUE},{AF_BLUE_DARK});color:#FFFFFF;
                padding:20px 24px;border-radius:10px;display:flex;align-items:center;gap:14px;">
      <div style="width:42px;height:42px;border-radius:50%;background:rgba(255,255,255,0.14);
                  display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:22px;">&#127968;</div>
      <div style="font-size:19px;font-weight:600;">{APP_TITLE}</div>
    </div>
    """


def render_disclaimer_html() -> str:
    return f"""
    <div style="background:{BG};border-bottom:1px solid {SILVER};padding:8px 24px;
                font-size:12px;color:#5F5E5A;font-style:italic;border-radius:0 0 10px 10px;">
      {DISCLAIMER_TEXT}
    </div>
    """


def render_metric_tile_html(label: str, count: int, risk_level: str) -> str:
    colors = risk_colors(risk_level)
    return f"""
    <div style="background:#FFFFFF;border-radius:8px;box-shadow:0 1px 4px rgba(0,0,0,0.08);
                display:flex;overflow:hidden;">
      <div style="width:4px;background:{colors['stripe']};"></div>
      <div style="padding:10px 12px;">
        <div style="font-size:12px;color:#888780;">{label}</div>
        <div style="font-size:22px;font-weight:600;color:#2C2C2A;">{count}</div>
      </div>
    </div>
    """


def render_section_header_html(label: str) -> str:
    return f"""
    <div class="afhn-section-header">{label}</div>
    <div class="afhn-section-underline"></div>
    """


def render_article_card_html(article: dict) -> str:
    risk_level = article.get("risk_level")
    colors = risk_colors(risk_level)
    badge_label = risk_level or "Unrated"
    icon = _RISK_ICON.get(risk_level, "?")
    title = article.get("title", "")
    summary = article.get("summary") or ""
    rationale = article.get("risk_rationale") or ""
    source = article.get("source", "")
    url = article.get("url", "#")
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

    return f"""
    <div class="afhn-card">
      <div class="afhn-card-stripe" style="background:{colors['stripe']};"></div>
      <div class="afhn-card-body">
        <div style="margin-bottom:4px;">
          <span class="afhn-badge" style="background:{colors['bg']};color:{colors['text']};">{icon} {badge_label}</span>
          <span style="font-size:14px;font-weight:600;color:#2C2C2A;">{title}</span>
        </div>
        {summary_html}
        {rationale_html}
        <div style="font-size:12px;color:#888780;">{meta} &middot; <a href="{url}" style="color:{AF_BLUE};">Read full article</a></div>
      </div>
    </div>
    """
