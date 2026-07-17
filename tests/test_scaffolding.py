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
