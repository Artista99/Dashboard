import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt

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
st.success(f"Access Granted. Welcome back, {user_info.get('name')}!")

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
    st.session_state.current_tab = "Charts"

col_tab1, col_tab2 = st.columns(2)

with col_tab1:
    if st.button("Charts View", use_container_width=True):
        st.session_state.current_tab = "Charts"
        st.rerun()

with col_tab2:
    if st.button("Edit Tickers", use_container_width=True):
        st.session_state.current_tab = "Edit Tickers"
        st.rerun()

st.markdown("---")


# =========================
# 5. CHARTS VIEW
# =========================

if st.session_state.current_tab == "Charts":

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
        </style>
    """, unsafe_allow_html=True)

    if tickers:

        with st.spinner("Fetching market data..."):
            df_all = get_market_data(tickers)

        for ticker in tickers:
            company_name = company_names.get(ticker, "Unknown Company")

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

                    st.subheader(f":{color}[{ticker} / {company_name} {price_info}]")

                    timeframe = st.radio(
                        "Timeframe",
                        options=["Max", "10y", "5y", "1y"],
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
                    else:
                        rule_dates = pd.date_range(
                            start=df_plot["Date"].min(),
                            end=df_plot["Date"].max(),
                            freq="MS"
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

    else:
        st.info("Add some stock symbols to your tickers.csv to get started.")


# =========================
# 6. EDIT TICKERS VIEW
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