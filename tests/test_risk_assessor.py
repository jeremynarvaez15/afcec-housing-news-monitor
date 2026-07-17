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
    def __init__(self, text, type="text"):
        self.text = text
        self.type = type


class _FakeThinkingBlock:
    """Simulates a reasoning/thinking content block that has no .text of its own."""
    type = "thinking"


class _FakeMessage:
    def __init__(self, text, content=None, stop_reason="end_turn"):
        self.content = content if content is not None else [_FakeContent(text)]
        self.stop_reason = stop_reason


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


class _RaisingMessages:
    def create(self, **kwargs):
        raise RuntimeError("AuthenticationError: invalid x-api-key")


class _RaisingClient:
    def __init__(self):
        self.messages = _RaisingMessages()


def test_assess_risk_captures_api_call_error_for_diagnostics(monkeypatch):
    import anthropic
    monkeypatch.setattr(anthropic, "Anthropic", lambda api_key: _RaisingClient())
    articles = [{"title": "Some story", "description": "desc", "url": "http://x"}]

    result = assess_risk(articles, api_key="fake-key")

    assert result[0]["risk_level"] is None
    assert "AuthenticationError" in result[0]["risk_error"]


def test_assess_risk_no_api_key_has_no_risk_error():
    articles = [{"title": "Some story", "description": "desc", "url": "http://x"}]

    result = assess_risk(articles, api_key="")

    assert result[0].get("risk_error") is None


class _MultiBlockMessages:
    def __init__(self, content, stop_reason="end_turn"):
        self._content = content
        self._stop_reason = stop_reason

    def create(self, **kwargs):
        return _FakeMessage(text=None, content=self._content, stop_reason=self._stop_reason)


class _MultiBlockClient:
    def __init__(self, content, stop_reason="end_turn"):
        self.messages = _MultiBlockMessages(content, stop_reason=stop_reason)


def test_assess_risk_skips_leading_thinking_block_to_find_text(monkeypatch):
    # Claude 5-family models can return a reasoning block ahead of the answer
    # text; content[0] is not guaranteed to be the text block.
    content = [_FakeThinkingBlock(), _FakeContent(_response_json(risk_level="High"))]
    import anthropic
    monkeypatch.setattr(anthropic, "Anthropic", lambda api_key: _MultiBlockClient(content))
    articles = [{"title": "Some story", "description": "desc", "url": "http://x"}]

    result = assess_risk(articles, api_key="fake-key")

    assert result[0]["risk_level"] == "High"
    assert result[0].get("risk_error") is None


def test_assess_risk_reports_clear_error_when_no_text_block_present(monkeypatch):
    content = [_FakeThinkingBlock()]
    import anthropic
    monkeypatch.setattr(anthropic, "Anthropic", lambda api_key: _MultiBlockClient(content))
    articles = [{"title": "Some story", "description": "desc", "url": "http://x"}]

    result = assess_risk(articles, api_key="fake-key")

    assert result[0]["risk_level"] is None
    assert "no text content" in result[0]["risk_error"].lower()


def test_assess_risk_parses_json_wrapped_in_markdown_code_fence(monkeypatch):
    fenced = "```json\n" + _response_json(risk_level="Medium") + "\n```"
    _patch_anthropic(monkeypatch, fenced)
    articles = [{"title": "Some story", "description": "desc", "url": "http://x"}]

    result = assess_risk(articles, api_key="fake-key")

    assert result[0]["risk_level"] == "Medium"
    assert result[0].get("risk_error") is None


def test_assess_risk_parses_json_prefaced_with_prose(monkeypatch):
    prefaced = "Here is the analysis:\n\n" + _response_json(risk_level="Low")
    _patch_anthropic(monkeypatch, prefaced)
    articles = [{"title": "Some story", "description": "desc", "url": "http://x"}]

    result = assess_risk(articles, api_key="fake-key")

    assert result[0]["risk_level"] == "Low"
    assert result[0].get("risk_error") is None


def test_assess_risk_reports_clear_error_when_text_block_is_empty(monkeypatch):
    # A text block that exists but is empty (e.g. output got cut off by
    # max_tokens before any visible answer was produced) must not silently
    # fall through to json.loads("") and surface a confusing JSONDecodeError.
    content = [_FakeContent("")]
    import anthropic
    monkeypatch.setattr(
        anthropic, "Anthropic", lambda api_key: _MultiBlockClient(content, stop_reason="max_tokens")
    )
    articles = [{"title": "Some story", "description": "desc", "url": "http://x"}]

    result = assess_risk(articles, api_key="fake-key")

    assert result[0]["risk_level"] is None
    assert "empty text block" in result[0]["risk_error"].lower()
    assert "max_tokens" in result[0]["risk_error"]
