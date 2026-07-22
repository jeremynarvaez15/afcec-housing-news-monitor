import feedparser
from datetime import datetime, timezone, timedelta

_RECENCY_HOURS = 336  # 14 days — widened from 7 days (which itself replaced an
# original 48h window that regularly missed real stories) to give even more
# margin against the same infrequent-coverage problem.

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
    # Google News search RSS: an unofficial but free endpoint that searches across
    # virtually every site Google News indexes, not just our hand-picked list.
    # entry.source.title (the real publisher, e.g. "Project On Government Oversight")
    # is used instead of this label wherever feedparser exposes it — see _fetch_feed.
    {
        "url": "https://news.google.com/rss/search?q=%22military%20housing%20privatization%22%20OR%20MHPI%20OR%20%22privatized%20military%20housing%22&hl=en-US&gl=US&ceid=US:en",
        "source": "Google News (broad web search)",
    },
    {
        # Bare "barracks" was tried first and matched too much unrelated content
        # (Vermont State Police stations are called "barracks," plus street names,
        # historical sites) — qualified phrases below cut that noise out.
        "url": "https://news.google.com/rss/search?q=%22military%20barracks%22%20OR%20%22Army%20barracks%22%20OR%20%22Air%20Force%20barracks%22%20OR%20%22Marine%20barracks%22%20OR%20%22military%20dorms%22%20OR%20%22DoD%20housing%22%20OR%20%22base%20housing%22&hl=en-US&gl=US&ceid=US:en",
        "source": "Google News (broad web search)",
    },
]

_TOPIC_KEYWORDS = {
    "mhpi", "military housing privatization", "privatized housing", "barracks",
    "dorms", "dormitory", "dod-owned housing", "dod owned housing", "base housing",
    "quality of life", "installation housing",
}

_PARTNER_NAMES = {
    "balfour beatty communities", "hunt military communities", "mayroad",
    "centinel", "burlington capital", "wright field development",
    "jl properties", "boyer hill", "the michaels organization",
}

_ADVOCACY_NAMES = {
    "change the air foundation", "project on government oversight",
    "national military family association",
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
    for name in _ADVOCACY_NAMES:
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
            entry_source = getattr(entry, "source", None)
            source_name = getattr(entry_source, "title", None) or feed_cfg["source"]
            articles.append({
                "title": title,
                "description": description[:500],
                "url": url,
                "source": source_name,
                "published_at": _parse_date(entry),
            })
        return articles
    except Exception:
        return []


def fetch_feed_diagnostics() -> list[dict]:
    """Per-feed fetch status for troubleshooting (entry counts, HTTP status,
    parse errors) independent of keyword/recency filtering. Not used on the
    normal render path — call this only when investigating why a feed isn't
    contributing articles, since it re-fetches every feed."""
    diagnostics = []
    for feed in _FEEDS:
        try:
            parsed = feedparser.parse(feed["url"])
            bozo = bool(getattr(parsed, "bozo", False))
            bozo_exception = getattr(parsed, "bozo_exception", None)
            diagnostics.append({
                "source": feed["source"],
                "url": feed["url"],
                "entry_count": len(parsed.entries),
                "http_status": getattr(parsed, "status", None),
                "error": str(bozo_exception) if bozo and bozo_exception else None,
            })
        except Exception as e:
            diagnostics.append({
                "source": feed["source"],
                "url": feed["url"],
                "entry_count": 0,
                "http_status": None,
                "error": str(e),
            })
    return diagnostics


def get_source_names() -> list[str]:
    """Unique source names monitored, in first-appearance order (some sources,
    like Stars and Stripes, have more than one feed URL in _FEEDS)."""
    seen = set()
    names = []
    for feed in _FEEDS:
        name = feed["source"]
        if name not in seen:
            seen.add(name)
            names.append(name)
    return names


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
