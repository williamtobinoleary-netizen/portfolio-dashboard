import importlib
import pandas as pd
import streamlit as st
import plotly.express as px
from utils.simulation import simulate_from_prices, evaluate_risk_profile
portfolio_module = importlib.import_module("utils.portfolio")
portfolio_module = importlib.reload(portfolio_module)
load_portfolio = portfolio_module.load_portfolio
number_rows_from_one = getattr(portfolio_module, "number_rows_from_one", None)
if number_rows_from_one is None:
    def number_rows_from_one(df):
        return df.reset_index(drop=True).set_index(pd.Index(range(1, len(df) + 1)))
download_prices = portfolio_module.download_prices
get_latest_prices = portfolio_module.get_latest_prices
metrics_module = importlib.import_module("utils.metrics")
position_values = metrics_module.position_values
daily_returns_from_prices = metrics_module.daily_returns_from_prices
portfolio_volatility = metrics_module.portfolio_volatility
sharpe_ratio = metrics_module.sharpe_ratio
portfolio_return_from_prices = getattr(metrics_module, "portfolio_return_from_prices", None)

if portfolio_return_from_prices is None:
    def portfolio_return_from_prices(price_dict):
        returns = {}
        for ticker, df in price_dict.items():
            if df is None or df.empty:
                returns[ticker] = None
            else:
                first = df['Close'].iloc[0]
                last = df['Close'].iloc[-1]
                if first == 0:
                    returns[ticker] = None
                else:
                    returns[ticker] = (last / first - 1) * 100
        return returns


def load_portfolio_from_upload(uploaded_file):
    if uploaded_file is None:
        return None
    try:
        return load_portfolio(uploaded_file)
    except Exception:
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file)

st.set_page_config(page_title="LSEG Portfolio Analytics")

st.title("LSEG Portfolio Analytics")

st.sidebar.header("Settings")
period = st.sidebar.selectbox("Price history", ["1y", "6mo", "3mo"], index=0)
refresh_clicked = st.sidebar.button("Refresh dashboard")
st.sidebar.caption("Edit portfolio.csv and press Refresh dashboard to update the view.")

uploaded_file = st.sidebar.file_uploader("Upload a portfolio CSV", type=["csv"])
st.sidebar.divider()
st.sidebar.subheader("Stock simulation")
simulation_ticker = st.sidebar.text_input("Ticker", value="AAPL")
simulation_amount = st.sidebar.number_input("Investment amount", min_value=100, value=1000, step=100)
simulation_horizon = st.sidebar.number_input("Horizon (years)", min_value=1, max_value=10, value=1, step=1)
if refresh_clicked:
    st.rerun()

st.header("Portfolio")
try:
    if uploaded_file is not None:
        df = load_portfolio_from_upload(uploaded_file)
        if df is None:
            raise ValueError("No portfolio data loaded from upload")
    else:
        df = load_portfolio("portfolio.csv")
except Exception as e:
    st.error(f"Could not load portfolio.csv: {e}")
    st.stop()

st.caption("Current portfolio input")
st.dataframe(number_rows_from_one(df), use_container_width=True)

tickers = df['Ticker'].tolist()
with st.spinner("Downloading market data..."):
    prices = download_prices(tickers, period=period)
latest = get_latest_prices(prices)

df_vals, total = position_values(df, latest)
total_shares = int(df['Shares'].sum())
returns = portfolio_return_from_prices(prices)

largest_position = df_vals.sort_values('Value', ascending=False).iloc[0]
if pd.notna(largest_position['Value']):
    top_ticker = largest_position['Ticker']
    top_value = largest_position['Value']
    top_weight = (top_value / total * 100) if total else 0
else:
    top_ticker = "N/A"
    top_value = 0
    top_weight = 0

portfolio_return = None
for ticker, value in returns.items():
    if value is not None:
        portfolio_return = value if portfolio_return is None else portfolio_return

st.subheader("Summary")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total portfolio value", f"£{total:,.2f}")
with col2:
    st.metric("Total shares", total_shares)
with col3:
    st.metric("Top holding", top_ticker)
with col4:
    st.metric("Top holding weight", f"{top_weight:.1f}%")

if portfolio_return is not None:
    st.metric("Portfolio return", f"{portfolio_return:.1f}%")

st.subheader("Holdings")
ordered_holdings = df_vals.sort_values('Value', ascending=False)
st.dataframe(number_rows_from_one(ordered_holdings), use_container_width=True)

st.subheader("Allocation")
fig = px.pie(df_vals, names='Ticker', values='Value', title='Portfolio allocation by holding')
st.plotly_chart(fig, use_container_width=True)

st.subheader("Stock simulation")
try:
    sim_prices = download_prices([simulation_ticker.strip().upper()], period="2y")
    sim_price_df = sim_prices.get(simulation_ticker.strip().upper())
    if sim_price_df is None or sim_price_df.empty:
        st.info("No price history was returned for that ticker yet.")
    else:
        sim_result = simulate_from_prices(sim_price_df, investment_amount=float(simulation_amount), horizon_years=int(simulation_horizon))
        st.metric("Ticker", simulation_ticker.strip().upper())
        st.metric("Projected value", f"£{sim_result['projected_value']:,.2f}")
        st.metric("Annualized return", f"{sim_result['annualized_return'] * 100:.2f}%")
        st.caption(f"Starting price: {sim_result['start_price']:.2f} — Ending price: {sim_result['end_price']:.2f}")
except Exception as exc:
    st.warning(f"Simulation unavailable: {exc}")

st.subheader("Risk profile")
risk_tolerance = st.slider("Risk tolerance", 1, 5, 3)
investment_horizon = st.slider("Investment horizon (years)", 1, 10, 5)
volatility = st.slider("Estimated volatility", 0.05, 0.60, 0.25, step=0.01)
profile = evaluate_risk_profile(risk_tolerance, investment_horizon, volatility)
st.write(f"**Suggested profile:** {profile['label']}")
st.write(f"**Time horizon:** {profile['horizon_label']}")
st.write(f"**Risk level:** {profile['risk_level']}")

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
    fig = px.line(dfp, y='Close', title=f"{t} price history")
    st.plotly_chart(fig, use_container_width=True)
