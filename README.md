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
  and NPR, keeps only articles matching housing keywords, known MHPI partner company
  names, or resident-advocacy/watchdog org names, drops anything older than 1 week.
- `app/data/risk_assessor.py` — sends each article to Claude
  (`claude-haiku-4-5-20251001`) for a summary + risk classification.
- `app/data/filters.py` — pure filter/sort/count helpers used by the sidebar.
- `app/ui/styles.py` — AF blue/silver themed HTML builders for the header, cards,
  and metric tiles.
- `app/ui/dashboard.py` — wires filters + styles + Streamlit widgets together.
- `main.py` — cached entry point (`streamlit run main.py`).
