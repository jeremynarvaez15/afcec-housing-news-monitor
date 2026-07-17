# AFCEC Military Housing News Monitor — Design Spec
**Date:** 2026-07-16
**Status:** Approved

---

## Goal

A standalone Streamlit app that monitors media coverage of military housing programs — MHPI, privatized housing, dorms, barracks, and DoD-owned housing — pulls from military/defense and general news sources, AI-summarizes each article, and assigns a Low/Medium/High/Critical risk level based on potential reputational or operational risk to the Air Force. Built for use as an AFCEC consultant; will be shared with colleagues.

---

## Scope

- New standalone repo and Streamlit Cloud deployment (not a tab in the existing swing-scanner app)
- Keyword-based monitoring only — no dedicated per-company sections
- Refreshes every 60 minutes (cached to control API costs)
- Articles retained for 48 hours from publish time, then drop out of the feed
- Requires one API key: `ANTHROPIC_API_KEY` (user already has one)
- No database — live snapshot only, backed by RSS recency filtering

---

## News Sources

RSS feeds only (no NewsAPI key required), pulled broadly then filtered by keyword match. Mirrors the `_fetch_feed` / `_categorize` pattern from the existing swing-scanner News Digest (`app/data/news_digest_fetcher.py`).

**Military/defense trade press:**
- Military.com
- Stars and Stripes
- Air Force Times
- Military Times
- Defense News
- DoD.gov press releases
- AF.mil news

**General news:**
- Reuters
- AP News
- NPR

(Exact RSS feed URLs to be resolved during implementation — some of the above may require finding the correct feed endpoint or an alternate general-news outlet if no public RSS feed exists.)

---

## Keyword Filtering

Articles are kept only if title or description matches one of:

**Program/topic terms:** "MHPI", "military housing privatization", "privatized housing", "barracks", "dorms", "dormitory", "DoD-owned housing", "base housing"

**Partner company names** (used purely as search keywords, not broken into their own UI sections):
- Balfour Beatty Communities
- Hunt Military Communities
- Mayroad
- Centinel
- Burlington Capital
- Wright Field Development
- JL Properties
- Boyer Hill
- The Michaels Organization

Matching should reuse the ambiguous-name/ticker-style guards from the existing fetcher (`_name_matches`) to avoid false positives on generic short names.

---

## AI Risk Assessment (Anthropic API)

Key: `ANTHROPIC_API_KEY` in `.streamlit/secrets.toml`.
Model: `claude-haiku-4-5-20251001`.

For each article, Claude returns:

```json
{
  "summary": "2-3 sentence plain-English summary of what happened",
  "risk_level": "High",
  "risk_rationale": "One short phrase: why this level",
  "af_specific": true
}
```

**risk_level rubric:**
- **Critical** — safety incidents/deaths, criminal charges, active congressional or IG investigation tied to housing
- **High** — mold/health hazard exposés, lawsuits, GAO reports, base-wide systemic problems
- **Medium** — tenant complaints, contractor disputes, funding/policy news, oversight hearings without findings yet
- **Low** — routine announcements, ribbon-cuttings, minor local coverage, general MHPI program news

**af_specific:** `true` if the story is explicitly about an Air Force or Space Force installation/program; `false` if it's about Army/Navy housing or DoD-wide MHPI policy (still relevant, but not AF-specific).

### Prompt template

```
You are a risk analyst for an Air Force Civil Engineer Center (AFCEC) consultant tracking
media coverage of military housing (MHPI, privatized housing, dorms, barracks, DoD-owned housing).

Headline: {title}
Content: {description or first 500 chars}

Return ONLY valid JSON with these exact keys:
- summary: 2-3 sentences explaining what happened and why it matters
- risk_level: one of "Critical", "High", "Medium", "Low" based on reputational/operational
  risk to the Air Force (Critical = safety incidents/deaths/criminal charges/active
  investigations; High = health hazard exposés/lawsuits/GAO reports/systemic base-wide
  problems; Medium = tenant complaints/contractor disputes/funding-policy news; Low =
  routine announcements/minor coverage)
- risk_rationale: short phrase explaining why this level was chosen
- af_specific: true if this story is explicitly about an Air Force or Space Force
  installation/program, false if about another service or DoD-wide policy
```

### Caching
- All assessments cached with `@st.cache_data(ttl=3600)` — 1 hour
- Claude API only called on cache miss (once per hour maximum)

---

## Visual Design & Branding

Goal: read as a credible, professional monitoring tool a client and team will trust — not a default-styled Streamlit demo.

**Color palette (Air Force blue & silver):**
- Primary/header: deep Air Force blue `#00308F`
- Accent/dividers: silver/light-gray `#C0C0C0`
- Background: white / very light gray `#F5F6F8`
- Risk colors layered on top of the neutral palette: Critical `#C0392B` (red), High `#E67E22` (orange), Medium `#D4AC0D` (yellow/gold), Low `#7F8C8D` (gray)
- No official DoD/Air Force insignia or seals are used (avoids implying official endorsement) — branding is color/typography only

**Implementation approach:** `st.set_page_config` with a wide layout, a `.streamlit/config.toml` `[theme]` block setting the base palette, plus targeted custom CSS injected via `st.markdown(..., unsafe_allow_html=True)` for card styling, pill-shaped risk badges, and the header bar. Kept in a single `app/ui/styles.py` module so styling stays out of layout logic.

**Header bar:** full-width band in Air Force blue (subtle two-tone gradient from `#00308F` to `#002266` for depth) with white text — a building/skyline icon (generic, not an official insignia) in a softly-tinted circular badge next to the app title "AFCEC Military Housing News Monitor," with a one-line tagline ("Media monitoring for Air Force Housing") below. No official DoD/Air Force seal, roundel, or insignia is used anywhere in the app — those are protected marks and using them on an unofficial tool could imply endorsement, which the disclaimer explicitly disclaims. No photography is used either (keeps the app lightweight and avoids image licensing/sourcing questions); the icon + color palette carry the visual identity. Disclaimer banner sits directly below the header, styled as a subtle callout (not alarming red) since it's a standing notice, not an error:
> "Unofficial personal tool for situational awareness — not an official AFCEC/Air Force system. AI-generated risk levels require human judgment before acting."

**Article cards:** white background, subtle drop shadow for elevation, thin left accent stripe colored by risk level (a common "status stripe" pattern), rounded corners. Risk level shown as a pill-shaped badge with a small icon (colored tint background, darker text of the same hue) rather than the plain-text `[score]` badges from the original digest — e.g. a warning-triangle icon on Critical/High, a dot on Medium/Low. Source and timestamp in muted gray, headline bold, "Read Full Article" as a styled link/button.

**Summary row:** rendered as four metric tiles (`st.metric` or custom CSS tiles) side by side rather than a single caption line — each tile has a subtle shadow, a colored accent stripe, and shows the count with the risk label above it.

**Section headers:** bold label with a short colored underline accent (Air Force blue) beneath it, replacing the plain `st.subheader` default styling, so each section reads as a distinct, designed block rather than default Streamlit text.

## Page Layout

Single page, wide layout, title "AFCEC Military Housing News Monitor."

**Header bar + disclaimer banner** as described above.

**Sidebar filters:**
- Risk level multi-select (Critical/High/Medium/Low, all checked by default)
- "Air Force/Space Force specific only" toggle
- Keyword search box (client-side filter on title/summary text of already-fetched articles)
- Sidebar also shows last-refreshed timestamp and a manual "Refresh now" button (bypasses cache)

**Summary row:** four metric tiles, e.g. `🔴 2 Critical · 🟠 5 High · 🟡 8 Medium · ⚪ 12 Low` (reflects post-filter counts)

### Section 1: 🏠 Housing Coverage Feed
- All articles passing the current sidebar filters, sorted Critical → High → Medium → Low
- Card format (styled per Visual Design above):
```
🔴 CRITICAL  Barracks mold exposure sickens airmen at [Base]
             Investigation launched after... [2-3 sentence summary]
             Why: health/safety hazard exposé
             Stars and Stripes · 3h ago · [Read Full Article →]
```
- Max 20 shown by default, rest in an expander (same pattern as existing digest)
- Empty state (no articles match filters): "No articles match the current filters."

### Section 2: ✈️ Air Force / Space Force Specific
- Same card format, filtered to `af_specific=true` (in addition to sidebar filters)
- Empty state: "No Air Force/Space Force-specific stories in the last hour. Check back soon."

---

## Data Flow

```
load_housing_news(cache_buster)          # @st.cache_data ttl=3600
  ├── fetch_housing_articles()           # RSS: military/defense + general feeds,
  │                                       #   filtered to housing keywords, 48h recency window
  └── assess_risk(articles)              # Anthropic API: per-article risk classification
        └── returns list[AssessedArticle]

render_dashboard(assessed_articles)      # app/ui/dashboard.py
  ├── render_summary_metrics()
  ├── render_main_feed()
  └── render_af_specific_feed()
```

---

## File Structure

```
afcec-housing-news-monitor/
├── main.py                        # Streamlit entry point
├── app/
│   ├── data/
│   │   ├── news_fetcher.py        # RSS feed list, fetch, keyword filter, 48h recency
│   │   └── risk_assessor.py       # Anthropic API risk classification + JSON parsing
│   └── ui/
│       ├── dashboard.py           # Header, sidebar filters, summary row, main feed, AF-specific feed
│       └── styles.py              # Theme colors, custom CSS (cards, badges, header bar)
├── .streamlit/
│   ├── config.toml                # Base Streamlit theme (Air Force blue/silver palette)
│   └── secrets.toml.example       # Documents required ANTHROPIC_API_KEY (not committed)
├── requirements.txt                # streamlit, feedparser, anthropic
└── README.md
```

---

## Error Handling

- If an individual RSS feed fails to fetch/parse: skip that feed silently, continue with the rest
- If Anthropic API key missing: show informational message "Add ANTHROPIC_API_KEY to your secrets to enable risk assessment"
- If Anthropic API call fails for an article: show raw headline + snippet without AI summary/risk level; do not crash
- If zero articles match keywords in the current window: show "No housing-related coverage found in the last 48 hours."

---

## Secrets Required

Add to Streamlit Cloud app secrets (`.streamlit/secrets.toml` locally):
```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

---

## Deployment

- New GitHub repo: `afcec-housing-news-monitor` under `jeremynarvaez15` (public, same as swing-scanner)
- New, separate Streamlit Cloud app deployment
- Local code: `C:\Users\jerem\OneDrive\Desktop\Claude\Claude Code\afcec-housing-news-monitor\`
