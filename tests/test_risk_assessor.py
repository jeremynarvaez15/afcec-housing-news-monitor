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
