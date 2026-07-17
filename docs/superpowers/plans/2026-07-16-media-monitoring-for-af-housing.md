# Media Monitoring for Air Force Housing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and locally verify a standalone Streamlit app that pulls military-housing-related news from RSS feeds, has Claude assess reputational/operational risk to the Air Force per article, and displays it in a styled, filterable dashboard — ready for a final manual push/deploy step.

**Architecture:** A `news_fetcher` module pulls and keyword-filters RSS articles; a `risk_assessor` module sends each article to the Anthropic API for a risk classification; pure `filters` functions handle sidebar filtering/sorting; pure `styles` functions build the HTML for the branded UI; `dashboard.py` wires filters + styles + Streamlit widgets together; `main.py` is the cached, cost-controlled entry point.

**Tech Stack:** Python 3.11, Streamlit ≥1.35.0, feedparser ≥6.0.0, anthropic ≥0.25.0, pytest.

## Global Constraints

- Python 3.11.
- `requirements.txt` pins: `streamlit>=1.35.0`, `feedparser>=6.0.0`, `anthropic>=0.25.0`.
- Anthropic model: `claude-haiku-4-5-20251001`.
- News cache: `@st.cache_data(ttl=3600)` (1 hour).
- Article recency window: 48 hours from publish time.
- App title (exact): `Media Monitoring for Air Force Housing`.
- Disclaimer text (exact): `This is an unofficial personal risk management tool, not an official Department of the Air Force system.`
- Color palette (exact hex): AF blue `#00308F`, AF blue dark `#002266`, silver `#C0C0C0`, background `#F5F6F8`; risk colors Critical `#C0392B`, High `#E67E22`, Medium `#D4AC0D`, Low `#7F8C8D`.
- No official DoD/Air Force seal, roundel, or insignia anywhere in the app. No photography.
- Secrets: `ANTHROPIC_API_KEY` only, read via `st.secrets.get("ANTHROPIC_API_KEY", "")`.
- Local project root: `C:\Users\jerem\OneDrive\Desktop\Claude\Claude Code\afcec-housing-news-monitor\`.
- Target GitHub repo (final task only): `afcec-housing-news-monitor` under `jeremynarvaez15`.
- Note on file structure: the approved spec's file list is extended with one file not originally listed, `app/data/filters.py`, to keep pure sidebar-filtering/sorting logic separately testable from Streamlit rendering code in `dashboard.py`. Everything else matches the spec's file structure.
- Note on RSS sources: the spec listed Reuters and AP News as general-news sources, but neither offers a public RSS feed anymore (confirmed live during planning). They are replaced with BBC News World (`feeds.bbci.co.uk`) and NPR is kept — this is the exact substitution the spec anticipated ("alternate general-news outlet if no public RSS feed exists"). Also note: `defense.gov` now redirects to `war.gov` (Department of War rename) — the DoD feed URL below is the live `war.gov` address.

---

## Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `.streamlit/config.toml`
- Create: `.streamlit/secrets.toml.example`
- Create: `app/__init__.py`
- Create: `app/data/__init__.py`
- Create: `app/ui/__init__.py`
- Create: `tests/__init__.py`
- Test: `tests/test_scaffolding.py`

**Interfaces:**
- Consumes: nothing (first task)
- Produces: package structure (`app`, `app.data`, `app.ui` importable packages) that every later task imports into; `requirements.txt` and `.streamlit/config.toml` that later tasks assume exist

- [ ] **Step 1: Write the failing scaffolding test**

Create `tests/test_scaffolding.py`:

```python
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_requirements_txt_lists_required_packages():
    content = (ROOT / "requirements.txt").read_text()
    assert "streamlit" in content
    assert "feedparser" in content
    assert "anthropic" in content


def test_streamlit_config_sets_af_blue_primary_color():
    config_path = ROOT / ".streamlit" / "config.toml"
    with open(config_path, "rb") as f:
        config = tomllib.load(f)
    assert config["theme"]["primaryColor"] == "#00308F"


def test_secrets_example_documents_anthropic_key():
    content = (ROOT / ".streamlit" / "secrets.toml.example").read_text()
    assert "ANTHROPIC_API_KEY" in content
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_scaffolding.py -v`
Expected: FAIL — `requirements.txt` (or the other files) don't exist yet (`FileNotFoundError`).

- [ ] **Step 3: Create the package structure and config files**

Create `app/__init__.py` (empty file).

Create `app/data/__init__.py` (empty file).

Create `app/ui/__init__.py` (empty file).

Create `tests/__init__.py` (empty file).

Create `requirements.txt`:

```
streamlit>=1.35.0
feedparser>=6.0.0
anthropic>=0.25.0
```

Create `.gitignore`:

```
.streamlit/secrets.toml
__pycache__/
*.pyc
.pytest_cache/
.env
.DS_Store
```

Create `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#00308F"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F5F6F8"
textColor = "#2C2C2A"
font = "sans serif"
```

Create `.streamlit/secrets.toml.example`:

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/test_scaffolding.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Install dependencies and confirm the environment is usable**

Run: `pip install -r requirements.txt`
Expected: installs without error.

Run: `pip show pytest` — if not installed, run `pip install pytest`.

- [ ] **Step 6: Commit**

```bash
git add app requirements.txt .gitignore .streamlit tests
git commit -m "$(cat <<'EOF'
Add project scaffolding for Media Monitoring for Air Force Housing

Package structure, requirements, gitignore, and Streamlit theme/secrets
config that later tasks build on.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: News Fetcher

**Files:**
- Create: `app/data/news_fetcher.py`
- Test: `tests/test_news_fetcher.py`

**Interfaces:**
- Consumes: `feedparser.parse(url)` (external library)
- Produces: `fetch_housing_articles() -> list[dict]` where each dict has keys `title: str`, `description: str`, `url: str`, `source: str`, `published_at: str` (ISO 8601). This is the exact shape Task 3 (`risk_assessor.assess_risk`) and Task 4/5/6 consume.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_news_fetcher.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_news_fetcher.py -v`
Expected: FAIL — `app/data/news_fetcher.py` does not exist (`ModuleNotFoundError`).

- [ ] **Step 3: Write the implementation**

Create `app/data/news_fetcher.py`:

```python
import feedparser
from datetime import datetime, timezone, timedelta

_RECENCY_HOURS = 48

# defense.gov redirects to war.gov (Department of War rename); this is the live URL.
_FEEDS = [
    {"url": "https://www.military.com/feed/", "source": "Military.com"},
    {"url": "https://subscribe.stripes.com/rss/top-news.xml", "source": "Stars and Stripes"},
    {"url": "https://subscribe.stripes.com/rss/us.xml", "source": "Stars and Stripes"},
    {"url": "https://www.airforcetimes.com/arc/outboundfeeds/rss/category/news/your-air-force/?outputType=xml", "source": "Air Force Times"},
    {"url": "https://www.militarytimes.com/arc/outboundfeeds/rss/?outputType=xml", "source": "Military Times"},
    {"url": "https://www.defensenews.com/arc/outboundfeeds/rss/", "source": "Defense News"},
    {"url": "https://www.war.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=945", "source": "Dept. of War News"},
    {"url": "https://www.af.mil/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=1", "source": "AF.mil"},
    {"url": "https://feeds.bbci.co.uk/news/world/rss.xml", "source": "BBC News"},
    {"url": "https://feeds.npr.org/1001/rss.xml", "source": "NPR"},
]

_TOPIC_KEYWORDS = {
    "mhpi", "military housing privatization", "privatized housing", "barracks",
    "dorms", "dormitory", "dod-owned housing", "dod owned housing", "base housing",
}

_PARTNER_NAMES = {
    "balfour beatty communities", "hunt military communities", "mayroad",
    "centinel", "burlington capital", "wright field development",
    "jl properties", "boyer hill", "the michaels organization",
}

_AMBIGUOUS_NAMES = {
    "dow", "general", "united", "american", "national", "digital",
    "global", "international", "first", "allied",
}


def _parse_date(entry) -> str:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                dt = datetime(*t[:6], tzinfo=timezone.utc)
                return dt.isoformat()
            except Exception:
                pass
    return datetime.now(timezone.utc).isoformat()


def _is_recent(entry, hours: int = _RECENCY_HOURS) -> bool:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                dt = datetime(*t[:6], tzinfo=timezone.utc)
                return datetime.now(timezone.utc) - dt < timedelta(hours=hours)
            except Exception:
                pass
    return True


def _name_matches(name: str, text: str) -> bool:
    """True only if the full name appears as a meaningful phrase in text."""
    name_lower = name.lower().strip()
    words = name_lower.split()
    if len(words) == 1 and (len(name_lower) <= 4 or name_lower in _AMBIGUOUS_NAMES):
        return False
    return name_lower in text


def _matches_keywords(title: str, description: str) -> bool:
    text = (title + " " + description).lower()
    for kw in _TOPIC_KEYWORDS:
        if kw in text:
            return True
    for name in _PARTNER_NAMES:
        if _name_matches(name, text):
            return True
    return False


def _fetch_feed(feed_cfg: dict) -> list[dict]:
    try:
        parsed = feedparser.parse(feed_cfg["url"])
        articles = []
        for entry in parsed.entries:
            if not _is_recent(entry):
                continue
            title = getattr(entry, "title", "") or ""
            description = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
            url = getattr(entry, "link", "") or ""
            if not title or not url:
                continue
            if not _matches_keywords(title, description):
                continue
            articles.append({
                "title": title,
                "description": description[:500],
                "url": url,
                "source": feed_cfg["source"],
                "published_at": _parse_date(entry),
            })
        return articles
    except Exception:
        return []


def fetch_housing_articles() -> list[dict]:
    articles = []
    for feed in _FEEDS:
        articles.extend(_fetch_feed(feed))
    seen = set()
    unique = []
    for a in articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)
    return unique
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_news_fetcher.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add app/data/news_fetcher.py tests/test_news_fetcher.py
git commit -m "$(cat <<'EOF'
Add RSS news fetcher with keyword and recency filtering

Pulls from military/defense trade press plus BBC and NPR, keeps only
articles matching MHPI/housing topic terms or known partner company
names, and drops anything older than 48 hours.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Risk Assessor

**Files:**
- Create: `app/data/risk_assessor.py`
- Test: `tests/test_risk_assessor.py`

**Interfaces:**
- Consumes: article dicts shaped like Task 2's output (`title`, `description` at minimum); the `anthropic` package's `Anthropic(api_key=...).messages.create(...)` API
- Produces: `assess_risk(articles: list[dict], api_key: str) -> list[dict]` — returns each input article dict merged with `summary: str`, `risk_level: str | None` (one of `"Critical"`, `"High"`, `"Medium"`, `"Low"`, or `None` if unassessed/unparseable), `risk_rationale: str`, `af_specific: bool`. This is the exact shape Task 4 (`filters.py`) and Task 5 (`styles.py`) consume.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_risk_assessor.py`:

```python
import json

from app.data.risk_assessor import assess_risk


def _response_json(risk_level="High", af_specific=True):
    return json.dumps({
        "summary": "Test summary of the article.",
        "risk_level": risk_level,
        "risk_rationale": "test rationale",
        "af_specific": af_specific,
    })


class _FakeContent:
    def __init__(self, text):
        self.text = text


class _FakeMessage:
    def __init__(self, text):
        self.content = [_FakeContent(text)]


class _FakeMessages:
    def __init__(self, response_text):
        self._response_text = response_text

    def create(self, **kwargs):
        return _FakeMessage(self._response_text)


class _FakeClient:
    def __init__(self, response_text):
        self.messages = _FakeMessages(response_text)


def _patch_anthropic(monkeypatch, response_text):
    import anthropic
    monkeypatch.setattr(anthropic, "Anthropic", lambda api_key: _FakeClient(response_text))


def test_assess_risk_parses_valid_response(monkeypatch):
    _patch_anthropic(monkeypatch, _response_json(risk_level="Critical", af_specific=True))
    articles = [{"title": "Mold found in barracks", "description": "Airmen sickened", "url": "http://x"}]

    result = assess_risk(articles, api_key="fake-key")

    assert len(result) == 1
    assert result[0]["risk_level"] == "Critical"
    assert result[0]["af_specific"] is True
    assert result[0]["summary"] == "Test summary of the article."
    assert result[0]["risk_rationale"] == "test rationale"
    assert result[0]["title"] == "Mold found in barracks"


def test_assess_risk_no_api_key_returns_fallback():
    articles = [{"title": "Some story", "description": "desc", "url": "http://x"}]

    result = assess_risk(articles, api_key="")

    assert result[0]["risk_level"] is None
    assert result[0]["summary"] == ""
    assert result[0]["af_specific"] is False


def test_assess_risk_invalid_json_falls_back(monkeypatch):
    _patch_anthropic(monkeypatch, "not valid json")
    articles = [{"title": "Some story", "description": "desc", "url": "http://x"}]

    result = assess_risk(articles, api_key="fake-key")

    assert result[0]["risk_level"] is None
    assert result[0]["summary"] == ""


def test_assess_risk_unrecognized_risk_level_becomes_none(monkeypatch):
    _patch_anthropic(monkeypatch, _response_json(risk_level="Severe"))
    articles = [{"title": "Some story", "description": "desc", "url": "http://x"}]

    result = assess_risk(articles, api_key="fake-key")

    assert result[0]["risk_level"] is None


def test_assess_risk_empty_articles_returns_empty_list():
    assert assess_risk([], api_key="fake-key") == []
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_risk_assessor.py -v`
Expected: FAIL — `app/data/risk_assessor.py` does not exist (`ModuleNotFoundError`).

- [ ] **Step 3: Write the implementation**

Create `app/data/risk_assessor.py`:

```python
import json

_PROMPT = """\
You are a risk analyst for an Air Force Civil Engineer Center (AFCEC) consultant tracking
media coverage of military housing (MHPI, privatized housing, dorms, barracks, DoD-owned housing).

Headline: {title}
Content: {content}

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
"""

_VALID_LEVELS = {"Critical", "High", "Medium", "Low"}

_FALLBACK = {
    "summary": "",
    "risk_level": None,
    "risk_rationale": "",
    "af_specific": False,
}


def _assess_one(client, article: dict) -> dict:
    content = (article.get("description") or "")[:500]
    prompt = _PROMPT.format(title=article["title"], content=content)
    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text.strip()
        parsed = json.loads(text)
        risk_level = str(parsed.get("risk_level", ""))
        if risk_level not in _VALID_LEVELS:
            risk_level = None
        return {
            "summary": str(parsed.get("summary", "")),
            "risk_level": risk_level,
            "risk_rationale": str(parsed.get("risk_rationale", "")),
            "af_specific": bool(parsed.get("af_specific", False)),
        }
    except Exception:
        return dict(_FALLBACK)


def assess_risk(articles: list[dict], api_key: str) -> list[dict]:
    """Enrich each article dict with an AI risk assessment. Safe to call with empty api_key."""
    if not api_key or not articles:
        return [{**a, **_FALLBACK} for a in articles]

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
    except Exception:
        return [{**a, **_FALLBACK} for a in articles]

    result = []
    for article in articles:
        enriched = dict(article)
        enriched.update(_assess_one(client, article))
        result.append(enriched)
    return result
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_risk_assessor.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add app/data/risk_assessor.py tests/test_risk_assessor.py
git commit -m "$(cat <<'EOF'
Add Anthropic-based risk assessor for housing news articles

Classifies each article as Critical/High/Medium/Low reputational or
operational risk to the Air Force, with a safe no-key/parse-failure
fallback that never crashes the app.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Filters and Sorting

**Files:**
- Create: `app/data/filters.py`
- Test: `tests/test_filters.py`

**Interfaces:**
- Consumes: article dicts shaped like Task 3's output (`risk_level: str | None`, `af_specific: bool`, `title: str`, `summary: str`)
- Produces:
  - `filter_by_risk_levels(articles: list[dict], levels: set[str]) -> list[dict]`
  - `filter_af_specific(articles: list[dict]) -> list[dict]`
  - `filter_by_keyword(articles: list[dict], query: str) -> list[dict]`
  - `sort_by_risk(articles: list[dict]) -> list[dict]`
  - `summary_counts(articles: list[dict]) -> dict[str, int]` (keys `"Critical"`, `"High"`, `"Medium"`, `"Low"`)

  These are the exact names Task 6 (`dashboard.py`) imports and calls.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_filters.py`:

```python
from app.data.filters import (
    filter_by_risk_levels,
    filter_af_specific,
    filter_by_keyword,
    sort_by_risk,
    summary_counts,
)


def _article(**overrides):
    base = {
        "title": "Test article",
        "summary": "Test summary",
        "risk_level": "Medium",
        "af_specific": False,
        "url": "http://example.com",
    }
    base.update(overrides)
    return base


def test_filter_by_risk_levels_keeps_only_selected_levels():
    articles = [_article(risk_level="Critical"), _article(risk_level="Low")]
    result = filter_by_risk_levels(articles, {"Critical"})
    assert len(result) == 1
    assert result[0]["risk_level"] == "Critical"


def test_filter_af_specific_keeps_only_af_specific_true():
    articles = [_article(af_specific=True), _article(af_specific=False)]
    result = filter_af_specific(articles)
    assert len(result) == 1
    assert result[0]["af_specific"] is True


def test_filter_by_keyword_matches_title_case_insensitive():
    articles = [
        _article(title="Mold found in barracks"),
        _article(title="Ribbon cutting ceremony"),
    ]
    result = filter_by_keyword(articles, "MOLD")
    assert len(result) == 1
    assert "Mold" in result[0]["title"]


def test_filter_by_keyword_empty_query_returns_all():
    articles = [_article(), _article()]
    result = filter_by_keyword(articles, "")
    assert len(result) == 2


def test_sort_by_risk_orders_critical_first():
    articles = [_article(risk_level="Low"), _article(risk_level="Critical"), _article(risk_level="Medium")]
    result = sort_by_risk(articles)
    assert [a["risk_level"] for a in result] == ["Critical", "Medium", "Low"]


def test_sort_by_risk_puts_unrated_last():
    articles = [_article(risk_level=None), _article(risk_level="High")]
    result = sort_by_risk(articles)
    assert result[0]["risk_level"] == "High"
    assert result[1]["risk_level"] is None


def test_summary_counts_tallies_each_level():
    articles = [_article(risk_level="Critical"), _article(risk_level="Critical"), _article(risk_level="Low")]
    counts = summary_counts(articles)
    assert counts == {"Critical": 2, "High": 0, "Medium": 0, "Low": 1}
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_filters.py -v`
Expected: FAIL — `app/data/filters.py` does not exist (`ModuleNotFoundError`).

- [ ] **Step 3: Write the implementation**

Create `app/data/filters.py`:

```python
_RISK_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}


def filter_by_risk_levels(articles: list[dict], levels: set[str]) -> list[dict]:
    return [a for a in articles if a.get("risk_level") in levels]


def filter_af_specific(articles: list[dict]) -> list[dict]:
    return [a for a in articles if a.get("af_specific")]


def filter_by_keyword(articles: list[dict], query: str) -> list[dict]:
    if not query:
        return list(articles)
    q = query.lower().strip()
    return [
        a for a in articles
        if q in (a.get("title", "") + " " + a.get("summary", "")).lower()
    ]


def sort_by_risk(articles: list[dict]) -> list[dict]:
    return sorted(articles, key=lambda a: _RISK_ORDER.get(a.get("risk_level"), 4))


def summary_counts(articles: list[dict]) -> dict:
    counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for a in articles:
        level = a.get("risk_level")
        if level in counts:
            counts[level] += 1
    return counts
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_filters.py -v`
Expected: PASS (7 passed)

- [ ] **Step 5: Commit**

```bash
git add app/data/filters.py tests/test_filters.py
git commit -m "$(cat <<'EOF'
Add pure filter/sort/count helpers for the housing news dashboard

Sidebar-facing logic (risk level, AF-specific, keyword search, sort,
summary counts) kept separate from Streamlit rendering so it can be
unit tested directly.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Styles

**Files:**
- Create: `app/ui/styles.py`
- Test: `tests/test_styles.py`

**Interfaces:**
- Consumes: article dicts shaped like Task 3's output
- Produces:
  - `APP_TITLE: str`, `DISCLAIMER_TEXT: str`, `AF_BLUE: str`, `RISK_COLORS: dict`
  - `risk_colors(risk_level: str | None) -> dict` (keys `"stripe"`, `"bg"`, `"text"`)
  - `time_ago(published_at: str) -> str`
  - `inject_base_styles() -> None` (calls `st.markdown`, not unit tested)
  - `render_header_html() -> str`
  - `render_disclaimer_html() -> str`
  - `render_metric_tile_html(label: str, count: int, risk_level: str) -> str`
  - `render_section_header_html(label: str) -> str`
  - `render_article_card_html(article: dict) -> str`

  These are the exact names Task 6 (`dashboard.py`) imports and calls.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_styles.py`:

```python
from datetime import datetime, timezone, timedelta

from app.ui import styles


def test_risk_colors_known_level():
    colors = styles.risk_colors("Critical")
    assert colors["stripe"] == "#C0392B"


def test_risk_colors_unknown_level_returns_fallback():
    colors = styles.risk_colors(None)
    assert colors["stripe"] == styles._UNKNOWN_COLOR["stripe"]


def test_render_header_html_contains_title_and_color():
    html = styles.render_header_html()
    assert styles.APP_TITLE in html
    assert styles.AF_BLUE in html


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


def test_time_ago_hours():
    published = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
    assert styles.time_ago(published) == "3h ago"


def test_time_ago_minutes():
    published = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
    assert styles.time_ago(published) == "15m ago"


def test_time_ago_empty_input_returns_empty_string():
    assert styles.time_ago("") == ""
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_styles.py -v`
Expected: FAIL — `app/ui/styles.py` does not exist (`ModuleNotFoundError`).

- [ ] **Step 3: Write the implementation**

Create `app/ui/styles.py`:

```python
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_styles.py -v`
Expected: PASS (10 passed)

- [ ] **Step 5: Commit**

```bash
git add app/ui/styles.py tests/test_styles.py
git commit -m "$(cat <<'EOF'
Add AF blue/silver themed HTML builders for header, cards, and tiles

Pure string-building functions (no Streamlit calls) so the visual
output is directly unit testable; inject_base_styles() is the only
function that touches st.markdown.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Dashboard and App Entry Point

**Files:**
- Create: `app/ui/dashboard.py`
- Create: `main.py`
- Test: `tests/test_main_app.py`

**Interfaces:**
- Consumes: `app.data.news_fetcher.fetch_housing_articles`, `app.data.risk_assessor.assess_risk`, `app.data.filters.{filter_by_risk_levels,filter_af_specific,filter_by_keyword,sort_by_risk,summary_counts}`, `app.ui.styles.{inject_base_styles,render_header_html,render_disclaimer_html,render_metric_tile_html,render_section_header_html,render_article_card_html}`
- Produces: `render_dashboard(articles: list[dict], key_missing: bool, last_refreshed: str) -> bool` (returns `True` if the user clicked "Refresh now"); `main.py` is the Streamlit entry point run via `streamlit run main.py`

- [ ] **Step 1: Write the failing smoke test**

Create `tests/test_main_app.py`:

```python
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
    # Force st.secrets.get to a known value regardless of any local secrets.toml,
    # so these tests are deterministic on every machine.
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_main_app.py -v`
Expected: FAIL — `main.py` does not exist (`FileNotFoundError` from `AppTest.from_file`).

- [ ] **Step 3: Write the dashboard implementation**

Create `app/ui/dashboard.py`:

```python
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


def render_dashboard(articles: list[dict], key_missing: bool, last_refreshed: str) -> bool:
    inject_base_styles()
    st.markdown(render_header_html(), unsafe_allow_html=True)
    st.markdown(render_disclaimer_html(), unsafe_allow_html=True)

    if key_missing:
        st.info("Add ANTHROPIC_API_KEY to your secrets to enable risk assessment.")

    selected_levels, af_only, query, refresh_clicked = _render_sidebar()
    st.sidebar.caption(f"Last refreshed: {last_refreshed}")

    if not articles:
        st.warning("No housing-related coverage found in the last 48 hours.")
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
        "No Air Force/Space Force-specific stories in the last hour. Check back soon.",
    )

    return refresh_clicked
```

- [ ] **Step 4: Write the app entry point**

Create `main.py`:

```python
import time

import streamlit as st

from app.data.news_fetcher import fetch_housing_articles
from app.data.risk_assessor import assess_risk
from app.ui.dashboard import render_dashboard

st.set_page_config(
    page_title="Media Monitoring for Air Force Housing",
    page_icon="🏠",
    layout="wide",
)

_REFRESH_INTERVAL = 3600


@st.cache_data(ttl=_REFRESH_INTERVAL)
def load_housing_news(_cache_buster: int):
    anthropic_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    articles = fetch_housing_articles()
    return assess_risk(articles, anthropic_key)


anthropic_key = st.secrets.get("ANTHROPIC_API_KEY", "")
cache_buster = int(time.time() // _REFRESH_INTERVAL)

with st.spinner("Loading housing news coverage..."):
    articles = load_housing_news(cache_buster)

last_refreshed = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
refresh_clicked = render_dashboard(
    articles, key_missing=(not anthropic_key), last_refreshed=last_refreshed
)

if refresh_clicked:
    load_housing_news.clear()
    st.rerun()
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `pytest tests/test_main_app.py -v`
Expected: PASS (3 passed). If `AppTest` behaves unexpectedly in this Streamlit version, use `superpowers:systematic-debugging` to diagnose before moving on — do not skip or delete the test.

- [ ] **Step 6: Manually verify the running app**

Run: `streamlit run main.py`

In the browser that opens:
1. Confirm the header shows "Media Monitoring for Air Force Housing" with the AF-blue gradient and building icon.
2. Confirm the disclaimer banner reads exactly: "This is an unofficial personal risk management tool, not an official Department of the Air Force system."
3. Confirm the sidebar has Critical/High/Medium/Low checkboxes (all checked), the "Air Force / Space Force specific only" checkbox, a search box, and a "Refresh now" button.
4. If no `.streamlit/secrets.toml` exists locally yet, confirm the "Add ANTHROPIC_API_KEY..." info message appears.
5. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`, fill in a real Anthropic API key, restart the app, and confirm articles load with colored risk badges, and that unchecking a risk level or typing in the search box changes what's shown.
6. Click "Refresh now" and confirm the app reloads without error.

Stop the app with `Ctrl+C` when done.

- [ ] **Step 7: Commit**

```bash
git add app/ui/dashboard.py main.py tests/test_main_app.py
git commit -m "$(cat <<'EOF'
Wire up dashboard rendering and the Streamlit app entry point

Sidebar filters drive the housing coverage feed and AF/SSF-specific
feed; main.py caches the fetch+assess pipeline hourly with a manual
refresh escape hatch.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: README and Deployment Prep

**Files:**
- Create: `README.md`

**Interfaces:**
- Consumes: nothing new (documents the finished app)
- Produces: instructions a future reader (or future Claude session) needs to run and deploy the app

- [ ] **Step 1: Write the README**

Create `README.md`:

```markdown
# Media Monitoring for Air Force Housing

An unofficial personal tool that monitors media coverage of military housing programs
— MHPI, privatized housing, dorms, barracks, and DoD-owned housing — summarizes each
article with Claude, and assigns a Critical/High/Medium/Low reputational/operational
risk rating for the Air Force. Built for use as an AFCEC consultant.

This is not an official Department of the Air Force system.

## Local setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in a
   real key from [console.anthropic.com](https://console.anthropic.com):
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
3. Run the app:
   ```
   streamlit run main.py
   ```

## Running tests

```
pytest
```

## Deployment (Streamlit Cloud)

1. Push this repo to GitHub (`afcec-housing-news-monitor` under `jeremynarvaez15`).
2. Go to [share.streamlit.io](https://share.streamlit.io), create a new app pointing
   at this repo's `main.py`.
3. In the app's Settings → Secrets, add:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
4. Deploy. The app refreshes its news feed hourly (cached) and has a manual
   "Refresh now" button in the sidebar for an immediate re-check.

## How it works

- `app/data/news_fetcher.py` — pulls RSS from military/defense trade press plus BBC
  and NPR, keeps only articles matching housing keywords or known MHPI partner
  company names, drops anything older than 48 hours.
- `app/data/risk_assessor.py` — sends each article to Claude
  (`claude-haiku-4-5-20251001`) for a summary + risk classification.
- `app/data/filters.py` — pure filter/sort/count helpers used by the sidebar.
- `app/ui/styles.py` — AF blue/silver themed HTML builders for the header, cards,
  and metric tiles.
- `app/ui/dashboard.py` — wires filters + styles + Streamlit widgets together.
- `main.py` — cached entry point (`streamlit run main.py`).
```

- [ ] **Step 2: Run the full test suite**

Run: `pytest -v`
Expected: all tests from Tasks 1–6 pass.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "$(cat <<'EOF'
Add README with setup, testing, and deployment instructions

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 4: Push to GitHub and deploy (requires explicit user confirmation)**

This step creates a public GitHub repo and a public Streamlit Cloud deployment —
confirm with the user before running. Do not run this step automatically.

```bash
gh repo create jeremynarvaez15/afcec-housing-news-monitor --public --source=. --remote=origin
git push -u origin main
```

Then walk the user through connecting the repo at
[share.streamlit.io](https://share.streamlit.io) and adding the `ANTHROPIC_API_KEY`
secret in the app's Settings, since that requires interacting with the Streamlit
Cloud UI directly.
