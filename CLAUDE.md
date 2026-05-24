# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

```bash
streamlit run app.py
```

The app runs on port 8501 by default. In GitHub Codespaces it starts automatically via `devcontainer.json`.

Install dependencies:
```bash
pip install -r requirements.txt
```

## Secrets configuration

The app requires a `.streamlit/secrets.toml` file (not in git). It needs:

```toml
[app_access]
allowed_emails = ["user@example.com"]

[auth]
# Google OAuth credentials for st.login("google")
redirect_uri = "http://localhost:8501/oauth2callback"
client_id = "..."
client_secret = "..."
```

Without this file the app will crash on startup when accessing `st.secrets`.

## Architecture

Single-file Streamlit app (`app.py`) with no backend or database. All state is ephemeral (session state + CSV file on disk).

**Auth gate (lines 12–29):** Uses Streamlit's built-in `st.user` / `st.login("google")` OAuth flow. Access is restricted to emails listed in `st.secrets["app_access"]["allowed_emails"]`. Everything below the gate only runs for authorized users.

**Data layer:** `tickers.csv` is the only persistent store — two columns (`Symbol`, `Company`). Market data is fetched live from Yahoo Finance via `yf.download()` and cached for 1 hour with `@st.cache_data(ttl=3600)`. The ticker list itself is cached indefinitely (cleared explicitly on save).

**Two views toggled via `st.session_state.current_tab`:**
- `"Charts"` — renders one Altair composite chart per ticker: a line chart layered with a price histogram, dashed vertical year/month gridlines, and a horizontal rule at the last close price annotated with a historical percentile label.
- `"Edit Tickers"` — raw text editor for `tickers.csv`; saving clears all `@st.cache_data` and switches back to Charts.

**Chart composition (lines 181–258):** Each chart is an `alt.layer(histogram, line, rules, hline, hline_text_bg, hline_text)` with `resolve_scale(x="independent")` so the histogram and line share the Y axis but have independent X axes.
