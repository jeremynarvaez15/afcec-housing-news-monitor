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
