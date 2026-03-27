# Contributing to Steam Stats Visualized

Thanks for your interest! Here's how to help.

## Quick Wins

- **Add game memes**: Edit `GAME_MEMES` in `src/analytics.py`. One-liner per game.
- **Add gaming personalities**: Edit `gaming_personality()` in `src/analytics.py`.
- **Fix bugs**: Check the [Issues](https://github.com/DrKenReid/steam-stats-visualized/issues) tab.

## Setup

```bash
git clone https://github.com/DrKenReid/steam-stats-visualized.git
cd steam-stats-visualized
pip install -r requirements.txt

# Get a Steam API key: https://steamcommunity.com/dev/apikey
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit with your key

streamlit run app.py
```

## Running Tests

```bash
pytest tests/ -v
```

## Code Structure

| File | What it does |
|------|-------------|
| `app.py` | UI layout only — no business logic |
| `src/steam_api.py` | All API calls + caching |
| `src/analytics.py` | Data processing + commentary |
| `src/charts.py` | Plotly chart builders |

## PR Guidelines

- Keep the humor. This isn't a corporate dashboard.
- Add tests for new analytics functions.
- Don't commit API keys or secrets.
- Dark theme only — we have standards.

## Feature Ideas

See the README for a list of potential features, or propose your own!
