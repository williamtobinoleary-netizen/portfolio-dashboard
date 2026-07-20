import streamlit as st
import plotly.express as px
from utils.portfolio import load_portfolio, download_prices, get_latest_prices
from utils.metrics import position_values, daily_returns_from_prices, portfolio_volatility, sharpe_ratio

st.set_page_config(page_title="Mini LSEG Portfolio Analytics")

st.title("Mini LSEG Portfolio Analytics Terminal")

st.sidebar.header("Settings")
period = st.sidebar.selectbox("Price history", ["1y", "6mo", "3mo"], index=0)

st.header("Portfolio")
try:
    df = load_portfolio("portfolio.csv")
except Exception as e:
    st.error(f"Could not load portfolio.csv: {e}")
    st.stop()

st.table(df)

tickers = df['Ticker'].tolist()
with st.spinner("Downloading market data..."):
    prices = download_prices(tickers, period=period)
latest = get_latest_prices(prices)

df_vals, total = position_values(df, latest)

st.subheader("Summary")
st.metric("Total portfolio value (approx)", f"£{total:,.2f}")

st.subheader("Holdings")
st.table(df_vals)

st.subheader("Allocation")
fig = px.pie(df_vals, names='Ticker', values='Value')
st.plotly_chart(fig, use_container_width=True)

st.subheader("Performance examples")
for t in tickers:
    dfp = prices.get(t)
    if dfp is None or dfp.empty:
        st.write(f"No data for {t}")
        continue
    returns = daily_returns_from_prices(dfp)
    vol = portfolio_volatility(returns)
    sr = sharpe_ratio(returns)
    st.write(f"**{t}** — Volatility: {vol:.2%}, Sharpe: {sr:.2f}")
    fig = px.line(dfp, y='Close', title=f"{t} Close Price")
    st.plotly_chart(fig, use_container_width=True)
