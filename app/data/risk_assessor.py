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


def _extract_text(message) -> str:
    """Return the first text-type content block's text. Claude 5-family models
    can return a leading reasoning/thinking block ahead of the answer, so the
    text block is not guaranteed to be content[0]."""
    stop_reason = getattr(message, "stop_reason", None)
    block_types = [getattr(b, "type", "unknown") for b in message.content]
    for block in message.content:
        if getattr(block, "type", None) == "text":
            text = (block.text or "").strip()
            if text:
                return text
            raise ValueError(
                f"Claude returned an empty text block (stop_reason={stop_reason}, "
                f"blocks={block_types})"
            )
    raise ValueError(
        f"Claude response had no text content block (stop_reason={stop_reason}, "
        f"blocks={block_types})"
    )


def _extract_json_object(text: str) -> str:
    """Pull the {...} object out of text that may be wrapped in a markdown code
    fence (```json ... ```) or prefaced with prose, both of which models commonly
    do even when told to "return ONLY valid JSON"."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return text  # nothing to extract; let json.loads raise its own error
    return text[start:end + 1]


def _assess_one(client, article: dict) -> dict:
    content = (article.get("description") or "")[:500]
    prompt = _PROMPT.format(title=article.get("title", ""), content=content)
    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        text = _extract_text(message)
        parsed = json.loads(_extract_json_object(text))
        risk_level = str(parsed.get("risk_level", ""))
        if risk_level not in _VALID_LEVELS:
            risk_level = None
        return {
            "summary": str(parsed.get("summary", "")),
            "risk_level": risk_level,
            "risk_rationale": str(parsed.get("risk_rationale", "")),
            "af_specific": bool(parsed.get("af_specific", False)),
        }
    except Exception as e:
        # risk_error is diagnostic-only (surfaced in a troubleshooting expander
        # when the dashboard notices articles coming back unrated with a key
        # present) — never assert on its exact wording, only that it exists.
        return {**_FALLBACK, "risk_error": f"{type(e).__name__}: {e}"}


def assess_risk(articles: list[dict], api_key: str) -> list[dict]:
    """Enrich each article dict with an AI risk assessment. Safe to call with empty api_key."""
    if not api_key or not articles:
        return [{**a, **_FALLBACK} for a in articles]

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
    except Exception as e:
        error = f"{type(e).__name__}: {e}"
        return [{**a, **_FALLBACK, "risk_error": error} for a in articles]

    result = []
    for article in articles:
        enriched = dict(article)
        enriched.update(_assess_one(client, article))
        result.append(enriched)
    return result
