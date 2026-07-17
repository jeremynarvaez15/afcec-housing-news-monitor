_RISK_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}


def filter_by_risk_levels(articles: list[dict], levels: set[str]) -> list[dict]:
    # An article with risk_level=None has no assessed level to filter by
    # (missing API key, or a failed AI call) — always keep it rather than
    # silently dropping content the sidebar's checkboxes can't represent.
    return [a for a in articles if a.get("risk_level") is None or a.get("risk_level") in levels]


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
