import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import altair as alt
from google import genai
from google.genai import types as genai_types

st.title("Ignacio's Dashboard")

# =========================
# 1. AUTHENTICATION
# =========================

if not st.user.is_logged_in:
    st.info("Please log in to access the application dashboard.")
    if st.button("Log in with Google", type="primary"):
        st.login("google")
    st.stop()

user_info = st.user
user_email = user_info.get("email", "").lower()
allowed_list = [email.lower() for email in st.secrets["app_access"]["allowed_emails"]]

if user_email not in allowed_list:
    st.error(f"Access Denied: The account {user_email} is not authorized to view this application.")
    if st.button("Log out / Switch Account"):
        st.logout()
    st.stop()

# Everything below is protected
# st.success(f"Access Granted. Welcome back, {user_info.get('name')}!")

if st.button("Log out"):
    st.logout()


# =========================
# 2. LOAD TICKERS FROM CSV
# =========================

@st.cache_data
def get_tickers_from_csv():
    df_csv = pd.read_csv("tickers.csv")
    tickers_list = df_csv["Symbol"].tolist()
    names_dict = dict(zip(df_csv["Symbol"], df_csv["Company"]))
    return tickers_list, names_dict


# =========================
# 3. FETCH MARKET DATA
# =========================

def pct_change_for_period(series, offset):
    if len(series) < 2:
        return None
    last = series.iloc[-1]
    cutoff = series.index.max() - offset
    past = series[series.index <= cutoff]
    if past.empty:
        return None
    return (last - past.iloc[-1]) / past.iloc[-1] * 100


@st.cache_data(ttl=3600)
def get_market_data(tickers_list):
    data = yf.download(tickers_list, period="max", auto_adjust=True)

    if len(tickers_list) == 1:
        return pd.DataFrame({tickers_list[0]: data["Close"]})

    return data["Close"]


# =========================
# 4. MAIN DASHBOARD
# =========================

st.markdown("---")
st.header("📈 Stock Price Tracker")

if "current_tab" not in st.session_state:
    st.session_state.current_tab = "Overview"

if "latest_news" not in st.session_state:
    try:
        with open("Latest_News.txt", "r") as _f:
            st.session_state.latest_news = _f.read()
    except FileNotFoundError:
        st.session_state.latest_news = ""

col_tab1, col_tab2, col_tab3 = st.columns(3)

with col_tab1:
    if st.button("Overview", use_container_width=True,
                 type="primary" if st.session_state.current_tab == "Overview" else "secondary"):
        st.session_state.current_tab = "Overview"
        st.rerun()

with col_tab2:
    if st.button("Charts View", use_container_width=True,
                 type="primary" if st.session_state.current_tab == "Charts" else "secondary"):
        st.session_state.current_tab = "Charts"
        st.rerun()

with col_tab3:
    if st.button("Edit Tickers", use_container_width=True,
                 type="primary" if st.session_state.current_tab == "Edit Tickers" else "secondary"):
        st.session_state.current_tab = "Edit Tickers"
        st.rerun()

st.markdown("---")


# =========================
# 5. OVERVIEW
# =========================

if st.session_state.current_tab == "Overview":

    try:
        tickers, company_names = get_tickers_from_csv()
    except FileNotFoundError:
        st.error("⚠️ tickers.csv not found. Please make sure it's in your project folder.")
        tickers = []
        company_names = {}

    if tickers:
        with st.spinner("Fetching market data..."):
            df_all = get_market_data(tickers)

        # --- News section ---
        if st.button("Fetch the Latest News"):
            ticker_list = ", ".join(tickers)
            prompt = (
                "Provide an overview to explain the latest stock development for the following tickers; "
                "provide the results in markdown; results should be to the point, explaining what might "
                "have moved the stock / ticker; if no clear information is available just skip that ticker; "
                "please provide the results in bullet point format, max 2 lines per ticker; "
                f"this is the list of tickers: {ticker_list}"
            )
            try:
                client = genai.Client(api_key=st.secrets["gemini"]["api_key"])
                with st.spinner("Fetching latest news from Gemini..."):
                    response = client.models.generate_content(
                        model="gemini-2.5-pro",
                        contents=prompt,
                        config=genai_types.GenerateContentConfig(
                            tools=[genai_types.Tool(google_search=genai_types.GoogleSearch())],
                        ),
                    )
                news_text = response.text
                with open("Latest_News.txt", "w") as f:
                    f.write(news_text)
                st.session_state.latest_news = news_text
            except Exception as e:
                st.error(f"Could not fetch news: {e}")

        if st.session_state.latest_news:
            st.markdown(st.session_state.latest_news)

        st.markdown("---")

        pct_cols = ["1d %", "1m %", "1y %", "5y %", "10y %"]

        rows = []
        for ticker in tickers:
            if ticker not in df_all.columns:
                continue
            s = df_all[ticker].dropna()
            company = company_names.get(ticker, "")
            rows.append({
                "Ticker / Company": f"{ticker} — {company}",
                "10y %": pct_change_for_period(s, pd.DateOffset(years=10)),
                "5y %":  pct_change_for_period(s, pd.DateOffset(years=5)),
                "1y %":  pct_change_for_period(s, pd.DateOffset(years=1)),
                "1m %":  pct_change_for_period(s, pd.DateOffset(months=1)),
                "1d %":  (s.iloc[-1] - s.iloc[-2]) / s.iloc[-2] * 100 if len(s) >= 2 else None,
            })

        def fmt(v):
            if v is None or pd.isna(v):
                return "N/A"
            sign = "+" if v >= 0 else ""
            return f"{sign}{v:.1f}%"

        def cell_color(v):
            if v is None or pd.isna(v):
                return ""
            return "color:green" if v >= 0 else "color:red"

        th = "padding:8px 16px; text-align:center; border-bottom:2px solid #ddd; font-weight:600;"
        td_label = "padding:8px 16px; border-bottom:1px solid #eee;"
        td_num = "padding:8px 16px; border-bottom:1px solid #eee; text-align:center;"

        html = f'<table style="width:100%; border-collapse:collapse;">'
        html += "<thead><tr>"
        for col in ["Ticker / Company"] + pct_cols:
            html += f'<th style="{th}">{col}</th>'
        html += "</tr></thead><tbody>"

        for row in rows:
            html += "<tr>"
            html += f'<td style="{td_label}">{row["Ticker / Company"]}</td>'
            for col in pct_cols:
                v = row[col]
                html += f'<td style="{td_num} {cell_color(v)}">{fmt(v)}</td>'
            html += "</tr>"

        html += "</tbody></table>"
        st.markdown(html, unsafe_allow_html=True)

    else:
        st.info("Add some stock symbols to your tickers.csv to get started.")


# =========================
# 6. CHARTS VIEW
# =========================

elif st.session_state.current_tab == "Charts":

    try:
        tickers, company_names = get_tickers_from_csv()
    except FileNotFoundError:
        st.error("⚠️ tickers.csv not found. Please make sure it's in your project folder.")
        tickers = []
        company_names = {}

    st.markdown("""
        <style>
            div[data-testid="stRadio"] {
                margin-top: -0.5rem !important;
                margin-bottom: -0.5rem !important;
            }
            div[data-testid="stColumn"]:first-of-type {
                position: sticky;
                top: 3.5rem;
                align-self: flex-start;
                max-height: calc(100vh - 4rem);
                overflow-y: auto;
            }
            [id^="chart-"] {
                scroll-margin-top: 4rem;
            }
        </style>
    """, unsafe_allow_html=True)

    if tickers:

        with st.spinner("Fetching market data..."):
            df_all = get_market_data(tickers)

        col_nav, col_charts = st.columns([1, 3])

        with col_nav:
            st.markdown("**Timeframe**")
            st.selectbox(
                "Timeframe",
                options=["Max", "10y", "5y", "1y", "1m", "1w"],
                key="global_tf",
                label_visibility="collapsed",
            )
            if st.session_state.get("_prev_global_tf") != st.session_state.global_tf:
                for t in tickers:
                    st.session_state[f"tf_{t}"] = st.session_state.global_tf
                st.session_state._prev_global_tf = st.session_state.global_tf

            st.markdown("**Tickers**")
            for ticker in tickers:
                company = company_names.get(ticker, "")
                if st.button(f"{ticker} — {company}", key=f"nav_{ticker}", use_container_width=True):
                    st.session_state.scroll_to = f"chart-{ticker}"

        with col_charts:
            for ticker in tickers:
                company_name = company_names.get(ticker, "Unknown Company")

                st.markdown(f'<div id="chart-{ticker}"></div>', unsafe_allow_html=True)

                if ticker in df_all.columns:
                    df_ticker = df_all[ticker].dropna()

                    if not df_ticker.empty:

                        price_info = ""
                        color = "green"

                        if len(df_ticker) >= 2:
                            last_close = df_ticker.iloc[-1]
                            prev_close = df_ticker.iloc[-2]
                            pct_change = ((last_close - prev_close) / prev_close) * 100
                            sign = "+" if pct_change > 0 else ""
                            price_info = f"/ {last_close:.2f} ({sign}{pct_change:.2f}%)"
                            color = "green" if pct_change >= 0 else "red"

                        elif len(df_ticker) == 1:
                            last_close = df_ticker.iloc[-1]
                            price_info = f"/ {last_close:.2f}"

                        with st.container(border=True):
                            st.markdown(f"**:{color}[{ticker} / {company_name} {price_info}]**")

                            timeframe = st.radio(
                                "Timeframe",
                                options=["Max", "10y", "5y", "1y", "1m", "1w"],
                                horizontal=True,
                                index=0,
                                key=f"tf_{ticker}",
                                label_visibility="collapsed"
                            )

                            df_plot_ticker = df_ticker.copy()

                            if timeframe == "1y":
                                cutoff_date = df_ticker.index.max() - pd.DateOffset(years=1)
                                df_plot_ticker = df_plot_ticker[df_plot_ticker.index >= cutoff_date]

                            elif timeframe == "5y":
                                cutoff_date = df_ticker.index.max() - pd.DateOffset(years=5)
                                df_plot_ticker = df_plot_ticker[df_plot_ticker.index >= cutoff_date]

                            elif timeframe == "10y":
                                cutoff_date = df_ticker.index.max() - pd.DateOffset(years=10)
                                df_plot_ticker = df_plot_ticker[df_plot_ticker.index >= cutoff_date]

                            elif timeframe == "1m":
                                cutoff_date = df_ticker.index.max() - pd.DateOffset(months=1)
                                df_plot_ticker = df_plot_ticker[df_plot_ticker.index >= cutoff_date]

                            elif timeframe == "1w":
                                cutoff_date = df_ticker.index.max() - pd.DateOffset(weeks=1)
                                df_plot_ticker = df_plot_ticker[df_plot_ticker.index >= cutoff_date]

                            df_plot = pd.DataFrame({
                                "Date": df_plot_ticker.index,
                                "Price": df_plot_ticker.values
                            })

                            if timeframe in ["Max", "10y", "5y"]:
                                rule_dates = pd.date_range(
                                    start=df_plot["Date"].min(),
                                    end=df_plot["Date"].max(),
                                    freq="YS"
                                )
                            elif timeframe == "1y":
                                rule_dates = pd.date_range(
                                    start=df_plot["Date"].min(),
                                    end=df_plot["Date"].max(),
                                    freq="MS"
                                )
                            elif timeframe == "1m":
                                rule_dates = pd.date_range(
                                    start=df_plot["Date"].min(),
                                    end=df_plot["Date"].max(),
                                    freq="W-MON"
                                )
                            else:
                                rule_dates = pd.date_range(
                                    start=df_plot["Date"].min(),
                                    end=df_plot["Date"].max(),
                                    freq="D"
                                )

                            df_rules = pd.DataFrame({"Date": rule_dates})

                            base_chart = alt.Chart(df_plot).mark_line().encode(
                                x=alt.X("Date:T", title="Date", axis=alt.Axis(orient="bottom")),
                                y=alt.Y("Price:Q", title="Price", scale=alt.Scale(zero=False))
                            )

                            rules = alt.Chart(df_rules).mark_rule(
                                color="gray",
                                strokeDash=[4, 4],
                                opacity=0.4
                            ).encode(
                                x=alt.X("Date:T", axis=None)
                            )

                            df_hline = pd.DataFrame({"Price": [last_close]})

                            hline = alt.Chart(df_hline).mark_rule(
                                color="blue",
                                opacity=0.6
                            ).encode(
                                y="Price:Q"
                            )

                            pct_below = (df_plot["Price"] <= last_close).mean() * 100

                            df_text = pd.DataFrame({
                                "Price": [last_close],
                                "Label": [f"{pct_below:.1f}%"]
                            })

                            hline_text_bg = alt.Chart(df_text).mark_text(
                                align="left",
                                baseline="bottom",
                                color="white",
                                stroke="white",
                                strokeWidth=4,
                                dx=5,
                                dy=-2,
                                fontWeight="bold"
                            ).encode(
                                y="Price:Q",
                                x=alt.value(0),
                                text="Label:N"
                            )

                            hline_text = alt.Chart(df_text).mark_text(
                                align="left",
                                baseline="bottom",
                                color="blue",
                                dx=5,
                                dy=-2,
                                fontWeight="bold"
                            ).encode(
                                y="Price:Q",
                                x=alt.value(0),
                                text="Label:N"
                            )

                            histogram = alt.Chart(df_plot).mark_bar(
                                color="lightblue",
                                opacity=0.4
                            ).encode(
                                y=alt.Y("Price:Q", bin=alt.Bin(maxbins=10), title=""),
                                x=alt.X("count():Q", title="", axis=None)
                            )

                            chart = alt.layer(
                                histogram,
                                base_chart,
                                rules,
                                hline,
                                hline_text_bg,
                                hline_text
                            ).resolve_scale(
                                x="independent"
                            ).configure_view(
                                stroke="black",
                                strokeWidth=1.5
                            )

                            st.altair_chart(chart, width="stretch")

                    else:
                        st.warning(f"No data found for {ticker}.")

                else:
                    st.warning(f"Ticker {ticker} not found in download results.")

        if st.session_state.get("scroll_to"):
            anchor = st.session_state.scroll_to
            st.session_state.scroll_to = None
            components.html(f"""
                <script>
                    setTimeout(function() {{
                        var el = window.parent.document.getElementById('{anchor}');
                        if (el) el.scrollIntoView({{behavior: 'smooth', block: 'start'}});
                    }}, 200);
                </script>
            """, height=0)

    else:
        st.info("Add some stock symbols to your tickers.csv to get started.")


# =========================
# 7. EDIT TICKERS VIEW
# =========================

elif st.session_state.current_tab == "Edit Tickers":

    st.subheader("Edit tickers.csv")

    try:
        with open("tickers.csv", "r") as f:
            current_content = f.read()
    except FileNotFoundError:
        current_content = "Symbol,Company\n"

    new_content = st.text_area(
        "Content",
        value=current_content,
        height=400,
        label_visibility="collapsed"
    )

    col_save, col_discard = st.columns(2)

    with col_save:
        if st.button("Save Changes", type="primary", use_container_width=True):
            with open("tickers.csv", "w") as f:
                f.write(new_content)

            st.cache_data.clear()
            st.session_state.current_tab = "Charts"
            st.rerun()

    with col_discard:
        if st.button("Discard", use_container_width=True):
            st.session_state.current_tab = "Charts"
            st.rerun()

    st.markdown("---")

    user_instruction = st.text_input(
        "Instructions",
        placeholder="e.g. Add NVDA and TSLA, remove AAPL, move MSFT to the top",
        label_visibility="collapsed",
    )

    col_ai, col_restore = st.columns(2)

    with col_ai:
        if st.button("Update Tickers with AI", type="primary", use_container_width=True):
            if not user_instruction.strip():
                st.warning("Please enter instructions before updating.")
            else:
                try:
                    with open("tickers.csv", "r") as f:
                        csv_content = f.read()
                except FileNotFoundError:
                    csv_content = "Symbol,Company\n"

                # Save backup before overwriting
                if "tickers_backup" not in st.session_state:
                    st.session_state.tickers_backup = csv_content

                prompt = (
                    "Please update this list of tickers based on the instructions on which tickers "
                    "to add or remove or move within the list; in your response please keep the same "
                    f"format; {user_instruction}\n\n{csv_content}"
                )
                try:
                    client = genai.Client(api_key=st.secrets["gemini"]["api_key"])
                    with st.spinner("Updating tickers with Gemini..."):
                        response = client.models.generate_content(
                            model="gemini-2.5-pro",
                            contents=prompt,
                            config=genai_types.GenerateContentConfig(
                                tools=[genai_types.Tool(google_search=genai_types.GoogleSearch())],
                            ),
                        )
                    updated_csv = response.text.strip()
                    # Strip markdown code fences if Gemini wraps the output
                    if updated_csv.startswith("```"):
                        lines = updated_csv.splitlines()
                        updated_csv = "\n".join(
                            l for l in lines if not l.startswith("```")
                        ).strip()
                    with open("tickers.csv", "w") as f:
                        f.write(updated_csv + "\n")
                    st.cache_data.clear()
                    st.success("tickers.csv updated. Reload the page or switch tabs to see changes.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not update tickers: {e}")

    with col_restore:
        if st.button("Restore", use_container_width=True):
            backup = st.session_state.get("tickers_backup")
            if backup:
                with open("tickers.csv", "w") as f:
                    f.write(backup)
                st.cache_data.clear()
                del st.session_state["tickers_backup"]
                st.success("Restored original tickers.csv.")
                st.rerun()
            else:
                st.warning("No backup found — nothing to restore.")