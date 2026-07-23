import importlib
from datetime import timedelta
from html import escape
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.simulation import evaluate_risk_profile, simulate_from_prices
from utils.ai_assistant import chat, build_system_prompt, get_portfolio_summary


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
metrics_module = importlib.reload(metrics_module)
position_values = metrics_module.position_values
daily_returns_from_prices = metrics_module.daily_returns_from_prices
portfolio_volatility = metrics_module.portfolio_volatility
sharpe_ratio = metrics_module.sharpe_ratio
portfolio_return_from_prices = getattr(metrics_module, "portfolio_return_from_prices", None)
portfolio_historical_performance = metrics_module.portfolio_historical_performance
project_future_value = metrics_module.project_future_value

if portfolio_return_from_prices is None:
    def portfolio_return_from_prices(price_dict):
        returns = {}
        for ticker, df in price_dict.items():
            if df is None or df.empty:
                returns[ticker] = None
            else:
                first = df["Close"].iloc[0]
                last = df["Close"].iloc[-1]
                returns[ticker] = None if first == 0 else (last / first - 1) * 100
        return returns


def load_portfolio_from_upload(uploaded_file):
    if uploaded_file is None:
        return None
    try:
        return load_portfolio(uploaded_file)
    except Exception:
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file)


st.set_page_config(
    page_title="LSEG Portfolio Analytics",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)


LSEG_COLORS = ["#F2F4F5", "#C4C9CE", "#90979E", "#686E74", "#44494E", "#B0B6BC"]

LSE_UNIVERSE = {
    "LSEG.L": "London Stock Exchange Group",
    "AZN.L": "AstraZeneca",
    "SHEL.L": "Shell",
    "HSBA.L": "HSBC Holdings",
    "ULVR.L": "Unilever",
    "BP.L": "BP",
    "GSK.L": "GSK",
    "BARC.L": "Barclays",
    "LLOY.L": "Lloyds Banking Group",
    "RR.L": "Rolls-Royce Holdings",
    "REL.L": "RELX",
    "NG.L": "National Grid",
    "DGE.L": "Diageo",
    "RIO.L": "Rio Tinto",
    "GLEN.L": "Glencore",
    "VOD.L": "Vodafone Group",
    "TSCO.L": "Tesco",
    "SBRY.L": "J Sainsbury",
    "BA.L": "BAE Systems",
    "AAL.L": "Anglo American",
    "STAN.L": "Standard Chartered",
    "LAND.L": "Land Securities Group",
}


@st.cache_data(ttl=900, show_spinner=False)
def load_company_news(ticker, limit=8):
    """Return a normalized list of recent Yahoo Finance stories."""
    try:
        import yfinance as yf

        stories = yf.Ticker(ticker).news or []
    except Exception:
        return []

    normalized = []
    for story in stories:
        content = story.get("content", story) or {}
        canonical_url = content.get("canonicalUrl") or {}
        click_url = content.get("clickThroughUrl") or {}
        url = (
            story.get("link")
            or content.get("link")
            or canonical_url.get("url")
            or click_url.get("url")
        )
        title = content.get("title") or story.get("title")
        provider = content.get("provider") or story.get("publisher") or "Yahoo Finance"
        if isinstance(provider, dict):
            provider = provider.get("displayName") or provider.get("name") or "Yahoo Finance"
        published = content.get("pubDate") or story.get("providerPublishTime")
        if title and url and urlparse(str(url)).scheme in {"http", "https"}:
            normalized.append(
                {
                    "title": str(title),
                    "url": str(url),
                    "provider": str(provider),
                    "published": published,
                }
            )
        if len(normalized) >= limit:
            break
    return normalized


def build_trend_forecast(price_frame, horizon=30, lookback=90):
    """Create a simple linear-trend illustration from recent closing prices."""
    if price_frame is None or price_frame.empty or len(price_frame) < 10:
        return None
    history = price_frame[["Close"]].dropna().tail(lookback).copy()
    if len(history) < 10:
        return None
    close = history["Close"].astype(float).to_numpy()
    x_values = np.arange(len(close), dtype=float)
    slope, intercept = np.polyfit(x_values, close, 1)
    future_x = np.arange(len(close), len(close) + horizon, dtype=float)
    last_date = pd.Timestamp(history.index[-1]).tz_localize(None)
    future_dates = pd.bdate_range(last_date + timedelta(days=1), periods=horizon)
    forecast = pd.DataFrame(
        {"Date": future_dates, "Price": np.maximum(intercept + slope * future_x, 0), "Series": "Trend forecast"}
    )
    historical = history.reset_index()
    historical.columns = ["Date", "Price"]
    historical["Date"] = pd.to_datetime(historical["Date"]).dt.tz_localize(None)
    historical["Series"] = "Historical close"
    return pd.concat([historical, forecast], ignore_index=True)

st.markdown(
    """
    <style>
        :root {
            --lseg-ink: #090a0b;
            --lseg-navy: #111315;
            --lseg-green: #d9dde1;
            --lseg-mint: #f0f2f4;
            --lseg-cloud: #e9ecef;
            --lseg-line: #747b82;
        }
        .stApp {
            background-color: #050506;
            background-image:
                radial-gradient(circle at 82% 5%, rgba(221, 226, 230, .14), transparent 28rem),
                radial-gradient(circle at 8% 75%, rgba(128, 134, 140, .10), transparent 25rem),
                linear-gradient(rgba(210, 215, 220, .035) 1px, transparent 1px),
                linear-gradient(90deg, rgba(210, 215, 220, .035) 1px, transparent 1px);
            background-size: auto, auto, 38px 38px, 38px 38px;
        }
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] p,
        [data-testid="stAppViewContainer"] label,
        [data-testid="stAppViewContainer"] .stMarkdown,
        [data-testid="stAppViewContainer"] [data-testid="stWidgetLabel"] {
            color: #d9dde1;
        }
        [data-testid="stAppViewContainer"] [data-baseweb="slider"] div,
        [data-testid="stAppViewContainer"] [data-baseweb="tab"] p,
        [data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"] p {
            color: #a9afb5;
        }
        [data-testid="stSidebar"] {
            background: rgba(4, 17, 27, .96);
            border-right: 1px solid rgba(220, 224, 228, .22);
        }
        [data-testid="stSidebar"],
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
            color: #f7fbfb;
        }
        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] [data-baseweb="select"] *,
        [data-testid="stSidebar"] [data-baseweb="input"] * { color: var(--lseg-ink); }
        [data-testid="stSidebar"] [data-baseweb="input"],
        [data-testid="stSidebar"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] [data-testid="stNumberInputContainer"] {
            background: #ffffff !important;
            border-color: #aeb3b8 !important;
        }
        [data-testid="stSidebar"] .stTextInput,
        [data-testid="stSidebar"] .stTextInput div,
        [data-testid="stSidebar"] .stTextInput div[data-baseweb="input"] {
            color-scheme: light;
        }
        [data-testid="stSidebar"] .stTextInput div[data-baseweb="input"] {
            background-color: #ffffff !important;
        }
        [data-testid="stSidebar"] .stTextInput input[type="text"] {
            background-color: #ffffff !important;
            caret-color: var(--lseg-ink) !important;
            color: var(--lseg-ink) !important;
            -webkit-text-fill-color: var(--lseg-ink) !important;
        }
        [data-testid="stSidebar"] .stTextInput input[type="text"]::placeholder {
            color: #6b7f87 !important;
            -webkit-text-fill-color: #6b7f87 !important;
            opacity: 1;
        }
        [data-testid="stSidebar"] [data-baseweb="input"] input,
        [data-testid="stSidebar"] [data-testid="stNumberInputContainer"] input {
            background: #ffffff;
            color: var(--lseg-ink) !important;
            -webkit-text-fill-color: var(--lseg-ink);
        }
        [data-testid="stSidebar"] [data-testid="stNumberInputStepDown"],
        [data-testid="stSidebar"] [data-testid="stNumberInputStepUp"] {
            background: #d8dcdf;
            color: var(--lseg-ink);
        }
        [data-testid="stSidebar"] [data-testid="stNumberInputStepDown"] svg,
        [data-testid="stSidebar"] [data-testid="stNumberInputStepUp"] svg,
        [data-testid="stSidebar"] [data-baseweb="select"] svg {
            fill: var(--lseg-ink);
        }
        [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.16); }
        [data-testid="stSidebar"] .stButton > button {
            background: var(--lseg-green);
            border: 0;
            color: #08090a;
            font-weight: 700;
        }
        .block-container { max-width: 1440px; padding-top: 1.6rem; padding-bottom: 3rem; }
        .hero {
            background:
                linear-gradient(118deg, rgba(5,6,7,.98) 0%, rgba(27,30,33,.96) 62%, rgba(89,95,101,.90) 100%);
            border: 1px solid rgba(229, 232, 235, .32);
            border-radius: 18px;
            box-shadow: 0 20px 60px rgba(0,0,0,.28), inset 0 1px 0 rgba(255,255,255,.06);
            color: white;
            margin-bottom: 1.35rem;
            overflow: hidden;
            padding: 2rem 2.25rem;
            position: relative;
        }
        .hero:after {
            background: linear-gradient(135deg, #fafafa, #777d83);
            border-radius: 50%;
            content: "";
            height: 190px;
            opacity: .18;
            position: absolute;
            right: -42px;
            top: -88px;
            width: 190px;
        }
        .hero__eyebrow { color: #e5e8eb; font-size: .76rem; font-weight: 800; letter-spacing: .16em; text-transform: uppercase; }
        .hero h1 { color: white; font-size: 2.15rem; letter-spacing: -.035em; margin: .35rem 0 .25rem; padding: 0; }
        .hero p { color: #d7e7e8; margin: 0; }
        [data-testid="stMetric"] {
            background: linear-gradient(145deg, rgba(38, 41, 44, .96), rgba(9, 10, 11, .97));
            border: 1px solid rgba(215, 220, 224, .22);
            border-radius: 12px;
            box-shadow: 0 12px 30px rgba(0,0,0,.18), inset 0 1px 0 rgba(255,255,255,.035);
            min-height: 112px;
            padding: 1rem 1.1rem;
        }
        [data-testid="stMetricLabel"] { color: #aeb4b9; font-weight: 650; }
        [data-testid="stMetricValue"] { color: #f4fbfb; }
        h2, h3 { color: #f3fbfb; letter-spacing: -.018em; }
        [data-testid="stDataFrame"], [data-testid="stPlotlyChart"] {
            background: rgba(12, 13, 15, .88);
            border: 1px solid rgba(215, 220, 224, .19);
            border-radius: 12px;
            box-shadow: 0 14px 34px rgba(0,0,0,.16);
            overflow: hidden;
        }
        .section-kicker { color: var(--lseg-mint); font-size: .74rem; font-weight: 800; letter-spacing: .15em; margin-bottom: -.7rem; text-shadow: 0 0 18px rgba(235,238,241,.22); text-transform: uppercase; }
        .profile-card {
            background: linear-gradient(135deg, rgba(185, 191, 197, .17), rgba(20, 22, 24, .94));
            border: 1px solid rgba(225, 229, 232, .22);
            border-left: 4px solid var(--lseg-mint);
            border-radius: 10px;
            box-shadow: 0 14px 34px rgba(0,0,0,.16);
            color: #edfafa;
            margin-top: .8rem;
            padding: 1rem 1.2rem;
        }
        .profile-card p { color: #edfafa !important; margin: .25rem 0; }
        .stTabs [data-baseweb="tab-list"] { gap: .35rem; }
        .stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0 0; padding: .7rem 1.1rem; }
        .stTabs [aria-selected="true"] { background: rgba(205,210,215,.16); color: #f1f3f5; }
        [data-testid="stExpander"] {
            background: rgba(12, 13, 15, .76);
            border-color: rgba(215, 220, 224, .17);
        }
        hr { border-color: rgba(215, 220, 224, .16) !important; }

        /* Y2K chrome finance system */
        .stApp {
            background-image:
                radial-gradient(ellipse at 76% -5%, rgba(116,157,205,.34), transparent 32rem),
                radial-gradient(ellipse at 3% 62%, rgba(63,84,126,.32), transparent 28rem),
                repeating-linear-gradient(0deg, rgba(255,255,255,.018) 0, rgba(255,255,255,.018) 1px, transparent 1px, transparent 4px),
                linear-gradient(rgba(210,215,220,.025) 1px, transparent 1px),
                linear-gradient(90deg, rgba(210,215,220,.025) 1px, transparent 1px),
                linear-gradient(145deg, #080d18 0%, #15243a 44%, #1d2d48 68%, #090c13 100%);
            background-size: auto, auto, auto, 42px 42px, 42px 42px, auto;
            font-family: "Arial", "Helvetica Neue", sans-serif;
        }
        [data-testid="stHeader"] { background: rgba(3,3,4,.72); backdrop-filter: blur(12px); }
        [data-testid="stSidebar"] {
            background: linear-gradient(90deg, rgba(255,255,255,.025) 1px, transparent 1px), linear-gradient(180deg, #050506 0%, #101215 50%, #050506 100%);
            background-size: 22px 22px, auto;
            box-shadow: 12px 0 44px rgba(0,0,0,.48), inset -1px 0 rgba(255,255,255,.12);
        }
        [data-testid="stSidebar"] .stButton > button {
            background: linear-gradient(180deg, #fff 0%, #c7ccd1 42%, #777e85 55%, #e7eaed 100%);
            border: 1px solid #f8f9fa;
            border-radius: 5px;
            box-shadow: inset 0 1px 0 white, inset 0 -1px 0 #565b60, 0 0 18px rgba(225,230,235,.12);
            color: #050506;
            letter-spacing: .045em;
            text-transform: uppercase;
        }
        [data-testid="stSidebar"] .stButton > button:hover { box-shadow: inset 0 1px 0 white, 0 0 24px rgba(225,230,235,.32); transform: translateY(-1px); }
        [data-testid="stSidebar"] [data-baseweb="input"],
        [data-testid="stSidebar"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] [data-testid="stNumberInputContainer"] {
            background: linear-gradient(180deg, #f8f9fa, #cbd0d5) !important;
            border: 1px solid #fff !important;
            border-radius: 4px !important;
            box-shadow: inset 0 1px 3px rgba(0,0,0,.28), 0 0 0 1px #555b61;
        }
        [data-testid="stSidebar"] .stTextInput input[type="text"],
        [data-testid="stSidebar"] [data-baseweb="input"] input,
        [data-testid="stSidebar"] [data-testid="stNumberInputContainer"] input { background: transparent !important; }
        .hero {
            background: radial-gradient(circle at 90% 5%, rgba(255,255,255,.20), transparent 17rem), linear-gradient(115deg, #030304 0%, #121519 48%, #555c63 100%);
            border: 1px solid #aeb4ba;
            border-radius: 8px;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.75), inset 0 -1px 0 rgba(0,0,0,.9), 0 0 0 1px #25282b, 0 22px 70px rgba(0,0,0,.52);
            isolation: isolate;
            padding: 2.2rem 2.35rem 1.8rem;
        }
        .hero:before { background: repeating-linear-gradient(90deg, transparent 0 13px, rgba(255,255,255,.07) 13px 14px); bottom: 0; content: ""; height: 4px; left: 0; position: absolute; width: 100%; }
        .hero:after {
            background: conic-gradient(from 215deg, #24282d, #f7f8f9, #555b61, #111315, #e9ecef, #24282d);
            border: 1px solid #f4f5f6;
            box-shadow: inset 0 0 22px rgba(0,0,0,.58), 0 0 38px rgba(235,238,241,.16);
            height: 210px;
            opacity: .82;
            right: -52px;
            top: -105px;
            width: 210px;
            z-index: -1;
        }
        .hero__eyebrow { color: #bfc5ca; font-family: "Courier New", monospace; font-size: .7rem; letter-spacing: .24em; }
        .hero h1 {
            background: linear-gradient(180deg, #fff 3%, #aeb4ba 43%, #f5f6f7 54%, #747b82 76%, #e8ebed 100%);
            background-clip: text;
            -webkit-background-clip: text;
            color: transparent;
            filter: drop-shadow(0 2px 0 #000);
            font-size: clamp(2.15rem, 4vw, 3.2rem);
            font-style: italic;
            font-weight: 900;
            letter-spacing: -.065em;
            line-height: 1;
            text-transform: uppercase;
        }
        .hero p { color: #c6cbd0; font-family: "Courier New", monospace; font-size: .82rem; }
        .hero__status { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: 1.25rem; }
        .hero__chip { background: linear-gradient(180deg, rgba(255,255,255,.14), rgba(255,255,255,.025)); border: 1px solid rgba(235,238,241,.32); border-radius: 2px; color: #e3e6e8; font-family: "Courier New", monospace; font-size: .62rem; letter-spacing: .12em; padding: .35rem .55rem; text-transform: uppercase; }
        .hero__chip:first-child:before { color: #f5f6f7; content: "●"; margin-right: .38rem; text-shadow: 0 0 8px white; }
        [data-testid="stMetric"] {
            background: linear-gradient(135deg, rgba(255,255,255,.09), transparent 38%), linear-gradient(160deg, #24282c 0%, #090a0b 58%, #16191c 100%);
            border: 1px solid #656c72;
            border-radius: 5px;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.34), 0 12px 34px rgba(0,0,0,.38);
            overflow: hidden;
            position: relative;
        }
        [data-testid="stMetric"]:after { background: linear-gradient(90deg, #4c5258, #f1f3f4, #555b61); bottom: 0; content: ""; height: 2px; left: 0; position: absolute; width: 100%; }
        [data-testid="stMetricLabel"] { font-family: "Courier New", monospace; font-size: .7rem; letter-spacing: .08em; text-transform: uppercase; }
        [data-testid="stMetricValue"] { font-weight: 800; letter-spacing: -.035em; }
        .section-kicker { color: #aeb4ba; font-family: "Courier New", monospace; letter-spacing: .22em; text-shadow: 0 0 16px rgba(255,255,255,.28); }
        h2, h3 { font-weight: 800; text-transform: uppercase; }
        [data-testid="stDataFrame"], [data-testid="stPlotlyChart"], [data-testid="stExpander"] { border-color: #555c62; border-radius: 5px; box-shadow: inset 0 1px 0 rgba(255,255,255,.12), 0 18px 42px rgba(0,0,0,.28); }
        .stTabs [data-baseweb="tab-list"] { border-bottom: 1px solid #737a81; gap: .15rem; }
        .stTabs [data-baseweb="tab"] { border: 1px solid transparent; border-radius: 3px 3px 0 0; font-family: "Courier New", monospace; letter-spacing: .055em; text-transform: uppercase; }
        .stTabs [aria-selected="true"] { background: linear-gradient(180deg, #dde1e4, #747b81) !important; border-color: #f5f6f7; }
        .stTabs [aria-selected="true"] p { color: #08090a !important; font-weight: 800; }
        .profile-card { background: linear-gradient(120deg, #31363b, #090a0b 65%); border-left: 4px solid #dfe3e6; border-radius: 4px; box-shadow: inset 0 1px 0 rgba(255,255,255,.18), 0 18px 42px rgba(0,0,0,.28); }

        /*
         * Theme-aware overrides. Streamlit changes these variables when the
         * user selects Light, Dark, or System from the app menu. Keep this
         * block last so the decorative terminal styling cannot lock the app
         * to a dark palette.
         */
        :root {
            color-scheme: normal;
            --dashboard-surface: color-mix(in srgb, var(--secondary-background-color) 88%, var(--background-color));
            --dashboard-raised: color-mix(in srgb, var(--secondary-background-color) 72%, var(--background-color));
            --dashboard-border: color-mix(in srgb, var(--text-color) 22%, transparent);
            --dashboard-muted: color-mix(in srgb, var(--text-color) 68%, transparent);
            --dashboard-shadow: color-mix(in srgb, var(--text-color) 15%, transparent);
        }
        .stApp {
            background-color: var(--background-color);
            background-image:
                radial-gradient(ellipse at 76% -5%, color-mix(in srgb, var(--primary-color) 16%, transparent), transparent 32rem),
                radial-gradient(ellipse at 3% 62%, color-mix(in srgb, var(--primary-color) 10%, transparent), transparent 28rem),
                linear-gradient(color-mix(in srgb, var(--text-color) 3%, transparent) 1px, transparent 1px),
                linear-gradient(90deg, color-mix(in srgb, var(--text-color) 3%, transparent) 1px, transparent 1px);
            background-size: auto, auto, 42px 42px, 42px 42px;
        }
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] p,
        [data-testid="stAppViewContainer"] label,
        [data-testid="stAppViewContainer"] .stMarkdown,
        [data-testid="stAppViewContainer"] [data-testid="stWidgetLabel"],
        [data-testid="stAppViewContainer"] [data-baseweb="slider"] div,
        [data-testid="stAppViewContainer"] [data-baseweb="tab"] p,
        [data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"] p,
        h2, h3 {
            color: var(--text-color);
        }
        [data-testid="stHeader"] {
            background: color-mix(in srgb, var(--background-color) 78%, transparent);
        }
        [data-testid="stSidebar"] {
            background: var(--secondary-background-color);
            border-right: 1px solid var(--dashboard-border);
            box-shadow: 12px 0 44px var(--dashboard-shadow);
        }
        [data-testid="stSidebar"],
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
            color: var(--text-color);
        }
        [data-testid="stMetric"],
        [data-testid="stDataFrame"],
        [data-testid="stPlotlyChart"],
        [data-testid="stExpander"] {
            background: var(--dashboard-surface);
            border-color: var(--dashboard-border);
            box-shadow: inset 0 1px 0 color-mix(in srgb, var(--text-color) 10%, transparent), 0 12px 34px var(--dashboard-shadow);
        }
        [data-testid="stMetricLabel"] { color: var(--dashboard-muted); }
        [data-testid="stMetricValue"] { color: var(--text-color); }
        [data-testid="stMetric"]:after {
            background: linear-gradient(90deg, var(--dashboard-border), var(--primary-color), var(--dashboard-border));
        }
        .hero {
            background: radial-gradient(circle at 90% 5%, color-mix(in srgb, var(--primary-color) 16%, transparent), transparent 17rem), var(--dashboard-raised);
            border-color: var(--dashboard-border);
            box-shadow: inset 0 1px 0 color-mix(in srgb, var(--text-color) 12%, transparent), 0 22px 55px var(--dashboard-shadow);
            color: var(--text-color);
        }
        .hero:after {
            background: conic-gradient(from 215deg, var(--secondary-background-color), var(--primary-color), var(--background-color), var(--text-color), var(--secondary-background-color));
            border-color: var(--dashboard-border);
            box-shadow: inset 0 0 22px var(--dashboard-shadow), 0 0 38px var(--dashboard-shadow);
        }
        .hero__eyebrow, .hero p, .hero__chip { color: var(--dashboard-muted); }
        .hero h1 {
            background: none;
            color: var(--text-color);
            filter: none;
        }
        .hero__chip {
            background: color-mix(in srgb, var(--secondary-background-color) 75%, transparent);
            border-color: var(--dashboard-border);
        }
        .section-kicker { color: var(--primary-color); text-shadow: none; }
        .profile-card {
            background: var(--dashboard-surface);
            border-color: var(--dashboard-border);
            border-left-color: var(--primary-color);
            box-shadow: 0 12px 34px var(--dashboard-shadow);
            color: var(--text-color);
        }
        .profile-card p { color: var(--text-color) !important; }
        .stTabs [data-baseweb="tab-list"] { border-bottom-color: var(--dashboard-border); }
        .stTabs [aria-selected="true"] {
            background: var(--secondary-background-color) !important;
            border-color: var(--dashboard-border);
        }
        .stTabs [aria-selected="true"] p { color: var(--text-color) !important; }
        .news-card {
            background: var(--dashboard-surface);
            border: 1px solid var(--dashboard-border);
            border-radius: 6px;
            margin: 0 0 .65rem;
            padding: .75rem .85rem;
        }
        .news-card a { color: var(--text-color); font-weight: 700; text-decoration: none; }
        .news-card a:hover { color: var(--primary-color); text-decoration: underline; }
        .news-card__meta { color: var(--dashboard-muted); font-size: .72rem; margin-top: .3rem; }
        /* Compact masthead: the market workspace is now the visual focus. */
        .hero {
            margin-bottom: .8rem;
            padding: .7rem 1.1rem;
        }
        .hero:before, .hero:after { display: none; }
        .hero__eyebrow { font-size: .58rem; line-height: 1; }
        .hero h1 {
            font-size: clamp(1.15rem, 2vw, 1.5rem);
            letter-spacing: -.025em;
            line-height: 1.15;
            margin: .2rem 0 .1rem;
        }
        .hero p { font-size: .7rem; line-height: 1.2; }
        .hero__status { display: none; }
        hr { border-color: var(--dashboard-border) !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <div class="hero__eyebrow">Portfolio intelligence</div>
        <h1>LSEG Portfolio Analytics</h1>
        <p>A consolidated view of portfolio value, allocation, performance and risk.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.header("Settings")
period = st.sidebar.selectbox("Price history", ["1y", "6mo", "3mo"], index=0)
refresh_clicked = st.sidebar.button("Refresh dashboard", use_container_width=True)
portfolio_source = st.sidebar.radio(
    "Portfolio source",
    ["Build in app", "Upload CSV", "Sample portfolio"],
    horizontal=False,
)

uploaded_file = None
built_portfolio = None
if portfolio_source == "Build in app":
    selected_tickers = st.sidebar.multiselect(
        "Select London-listed companies",
        options=list(LSE_UNIVERSE),
        default=["LSEG.L", "AZN.L", "SHEL.L"],
        format_func=lambda ticker: f"{LSE_UNIVERSE[ticker]} · {ticker}",
        help="Choose one or more holdings, then set the number of shares below.",
    )
    portfolio_rows = []
    with st.sidebar.expander("Set holding sizes", expanded=True):
        for selected_ticker in selected_tickers:
            shares = st.number_input(
                f"{LSE_UNIVERSE[selected_ticker]} ({selected_ticker})",
                min_value=0.0,
                value=10.0,
                step=1.0,
                key=f"portfolio_shares_{selected_ticker}",
            )
            if shares > 0:
                portfolio_rows.append({"Ticker": selected_ticker, "Shares": shares})
    built_portfolio = pd.DataFrame(portfolio_rows, columns=["Ticker", "Shares"])
    st.sidebar.caption("Your dashboard updates automatically when holdings change.")
elif portfolio_source == "Upload CSV":
    uploaded_file = st.sidebar.file_uploader("Upload a portfolio CSV", type=["csv"])
    st.sidebar.caption("The CSV must contain Ticker and Shares columns.")
else:
    st.sidebar.caption("Using the holdings stored in portfolio.csv.")

st.sidebar.divider()
st.sidebar.subheader("Stock simulation")
simulation_ticker = st.sidebar.text_input("Ticker", value="AAPL")
simulation_amount = st.sidebar.number_input("Investment amount", min_value=100, value=1000, step=100)
simulation_horizon = st.sidebar.number_input("Horizon (years)", min_value=1, max_value=10, value=1, step=1)
if refresh_clicked:
    st.rerun()

try:
    if portfolio_source == "Build in app":
        if built_portfolio is None or built_portfolio.empty:
            st.info("Select at least one company and enter a share amount greater than zero.")
            st.stop()
        df = built_portfolio
    elif portfolio_source == "Upload CSV" and uploaded_file is not None:
        df = load_portfolio_from_upload(uploaded_file)
        if df is None:
            raise ValueError("No portfolio data loaded from upload")
    elif portfolio_source == "Upload CSV":
        st.info("Upload a portfolio CSV to continue, or choose another portfolio source.")
        st.stop()
    else:
        df = load_portfolio("portfolio.csv")
except Exception as exc:
    st.error(f"Could not load portfolio.csv: {exc}")
    st.stop()

tickers = df["Ticker"].tolist()
with st.spinner("Downloading market data..."):
    prices = download_prices(tickers, period=period)
latest = get_latest_prices(prices)

# Yahoo commonly reports London-listed equities in GBp (pence). Normalize
# these quotes to GBP so portfolio values match the pound-denominated display.
for ticker, latest_price in latest.items():
    if ticker.endswith(".L") and latest_price is not None:
        latest[ticker] = latest_price / 100

df_vals, total = position_values(df, latest)
total_shares = int(df["Shares"].sum())
returns = portfolio_return_from_prices(prices)
historical_performance = portfolio_historical_performance(df, prices)
largest_position = df_vals.sort_values("Value", ascending=False).iloc[0]
if pd.notna(largest_position["Value"]):
    top_ticker = largest_position["Ticker"]
    top_value = largest_position["Value"]
    top_weight = (top_value / total * 100) if total else 0
else:
    top_ticker, top_value, top_weight = "N/A", 0, 0

portfolio_return = (
    historical_performance["total_return"] * 100
    if historical_performance is not None
    else None
)

st.markdown('<div class="section-kicker">Market intelligence</div>', unsafe_allow_html=True)
st.subheader("Company outlook and latest news")
outlook_column, news_column = st.columns([1.65, 0.85], gap="large")

with news_column:
    intelligence_ticker = st.selectbox(
        "Company news",
        options=list(LSE_UNIVERSE),
        format_func=lambda ticker: f"{LSE_UNIVERSE[ticker]} · {ticker}",
        key="intelligence_company",
        help="Choose any company from the available London-listed universe.",
    )
    st.markdown("#### Latest headlines")
    company_news = load_company_news(intelligence_ticker)
    if company_news:
        for story in company_news:
            published = story["published"]
            if isinstance(published, (int, float)):
                published_label = pd.to_datetime(published, unit="s", utc=True).strftime("%d %b %Y, %H:%M UTC")
            elif published:
                parsed_date = pd.to_datetime(published, utc=True, errors="coerce")
                published_label = parsed_date.strftime("%d %b %Y, %H:%M UTC") if pd.notna(parsed_date) else "Recent"
            else:
                published_label = "Recent"
            st.markdown(
                f"""
                <div class="news-card">
                    <a href="{escape(story['url'], quote=True)}" target="_blank" rel="noopener noreferrer">{escape(story['title'])}</a>
                    <div class="news-card__meta">{escape(story['provider'])} · {published_label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No recent headlines are available for this company right now.")

with outlook_column:
    st.markdown(f"#### {LSE_UNIVERSE[intelligence_ticker]} market view")
    if intelligence_ticker in prices and prices[intelligence_ticker] is not None and not prices[intelligence_ticker].empty:
        intelligence_prices = prices[intelligence_ticker]
    else:
        with st.spinner("Loading company price history..."):
            intelligence_prices = download_prices([intelligence_ticker], period="1y").get(intelligence_ticker)

    forecast_frame = build_trend_forecast(intelligence_prices)
    if forecast_frame is None:
        st.info("There is not enough price history to produce this market view.")
    else:
        historical_series = forecast_frame[forecast_frame["Series"] == "Historical close"]
        forecast_series = forecast_frame[forecast_frame["Series"] == "Trend forecast"]
        latest_close = historical_series["Price"].iloc[-1]
        forecast_close = forecast_series["Price"].iloc[-1]
        forecast_change = (forecast_close / latest_close - 1) * 100 if latest_close else 0
        outlook_metrics = st.columns(3)
        outlook_metrics[0].metric("Latest close", f"{latest_close:,.2f} GBp")
        outlook_metrics[1].metric("30-day trend", f"{forecast_close:,.2f} GBp", f"{forecast_change:+.1f}%")
        outlook_metrics[2].metric("Forecast window", "30 trading days")

        outlook_figure = px.line(
            forecast_frame,
            x="Date",
            y="Price",
            color="Series",
            title=f"{intelligence_ticker} historical close and trend projection",
            color_discrete_map={"Historical close": "#4f8fd8", "Trend forecast": "#e09f3e"},
        )
        outlook_figure.update_traces(line_width=2.5)
        outlook_figure.update_traces(
            selector=dict(name="Trend forecast"),
            line=dict(dash="dash", width=3),
        )
        outlook_figure.update_layout(
            margin=dict(l=20, r=20, t=55, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis_title=None,
            yaxis_title="Price (GBp)",
            legend_title_text=None,
            hovermode="x unified",
        )
        st.plotly_chart(outlook_figure, use_container_width=True)

        momentum_20d = (
            (latest_close / historical_series["Price"].iloc[-21] - 1) * 100
            if len(historical_series) >= 21 and historical_series["Price"].iloc[-21]
            else 0.0
        )
        signal_score = int(forecast_change > 2) + int(momentum_20d > 2)
        signal_score -= int(forecast_change < -2) + int(momentum_20d < -2)
        if signal_score >= 2:
            market_outlook, action_signal = "Bullish", "Leans buy"
            signal_message = "Both the recent momentum and projected trend are positive. Consider researching valuation, results and downside risk before acting."
            signal_display = st.success
        elif signal_score <= -2:
            market_outlook, action_signal = "Bearish", "Leans sell"
            signal_message = "Both the recent momentum and projected trend are negative. Consider reviewing the investment case, risk limits and upcoming company events."
            signal_display = st.error
        else:
            market_outlook, action_signal = "Neutral / mixed", "Hold and watch"
            signal_message = "The trend indicators do not agree strongly enough to establish a clear direction. Waiting for more evidence may be appropriate."
            signal_display = st.info

        st.markdown("#### Projection-based research signal")
        signal_columns = st.columns(4)
        signal_columns[0].metric("Market outlook", market_outlook)
        signal_columns[1].metric("Model signal", action_signal)
        signal_columns[2].metric("20-day momentum", f"{momentum_20d:+.1f}%")
        signal_columns[3].metric("Projected trend", f"{forecast_change:+.1f}%")
        signal_display(signal_message)
        st.caption(
            "The dashed line is a simple linear trend based on up to 90 recent closes. "
            "The buy, hold or sell wording is a mechanical research indicator based only on the two displayed trends; "
            "it is not personalised financial advice or a price target. Headlines are supplied by Yahoo Finance."
        )

st.divider()
st.markdown('<div class="section-kicker">Portfolio overview</div>', unsafe_allow_html=True)
st.subheader("Summary")
summary_columns = st.columns(5)
summary_columns[0].metric(
    "Total portfolio value",
    f"£{total:,.2f}",
    help="The latest available price of every holding multiplied by its share quantity, then added together. London quotes are converted from pence to pounds.",
)
summary_columns[1].metric(
    "Total shares",
    total_shares,
    help="The combined number of shares across all holdings. This does not describe diversification because different shares have different prices.",
)
summary_columns[2].metric(
    "Top holding",
    top_ticker,
    help="The company with the largest current monetary value in this portfolio.",
)
summary_columns[3].metric(
    "Top holding weight",
    f"{top_weight:.1f}%",
    help="The percentage of total portfolio value concentrated in the largest holding. A high figure can indicate concentration risk.",
)
summary_columns[4].metric(
    "Portfolio return",
    f"{portfolio_return:.1f}%" if portfolio_return is not None else "N/A",
    help="The estimated change in value across the selected price-history period, assuming today’s share quantities were held throughout. It covers the whole portfolio and excludes fees, taxes, dividends, and currency effects.",
)

with st.expander("Portfolio · Current portfolio input"):
    st.dataframe(number_rows_from_one(df), use_container_width=True)

with st.expander("How to read the portfolio summary"):
    st.markdown(
        """
        **Portfolio return** compares the estimated starting and ending values of the complete portfolio over the selected price-history period. A positive result means its market value rose; a negative result means it fell.

        **Annualized return** converts that performance into an equivalent yearly compound rate, making different time periods easier to compare. It is not a forecast.

        **Holding weight** shows how much each company contributes to total value. Concentrated portfolios can move more sharply when their largest holdings change price.

        Prices may be delayed. Calculations exclude trading fees, tax, dividends, inflation and, for portfolios mixing markets, currency movements.
        """
    )

st.divider()
st.markdown('<div class="section-kicker">Analytics workspace</div>', unsafe_allow_html=True)
st.subheader("Portfolio analysis")
projection_tab, simulation_tab, risk_tab, performance_tab, ai_tab = st.tabs(
    ["Portfolio projection", "Stock simulation", "Risk profile", "Performance examples", "AI assistant"]
)

with projection_tab:
    st.subheader("Portfolio return and projection")
    if historical_performance is None:
        st.info("There is not enough price history to calculate a portfolio projection.")
    else:
        historical_cagr = historical_performance["annualized_return"]
        controls_column, explanation_column = st.columns([1.15, 0.85], gap="large")
        with controls_column:
            projection_years = st.slider(
                "Projection horizon (years)",
                1,
                30,
                5,
                help="How many years the compound-growth illustration should cover.",
            )
            default_rate = float(min(max(historical_cagr * 100, -20.0), 30.0))
            assumed_return = st.slider(
                "Assumed annual return",
                -20.0,
                30.0,
                default_rate,
                step=0.5,
                format="%.1f%%",
                help="The yearly growth assumption used in the projection. It defaults to the portfolio’s annualized historical rate but can be changed.",
            )
            monthly_contribution = st.number_input(
                "Monthly contribution",
                min_value=0.0,
                value=0.0,
                step=50.0,
                help="An optional amount added at the end of every month.",
            )
            target_return = st.slider(
                "Target annual return",
                0.0,
                20.0,
                5.0,
                step=0.5,
                format="%.1f%%",
                help="Your own comparison threshold. It is not a market benchmark or recommendation.",
            )

        assumed_rate = assumed_return / 100
        projected_value = project_future_value(
            total, assumed_rate, projection_years, monthly_contribution
        )
        total_contributed = total + monthly_contribution * projection_years * 12
        estimated_gain = projected_value - total_contributed

        with explanation_column:
            st.markdown(
                f"""
                <div class="profile-card">
                    <p><strong>Selected-period return:</strong> {portfolio_return:.2f}%</p>
                    <p><strong>Historical annualized return:</strong> {historical_cagr * 100:.2f}%</p>
                    <p><strong>Projection assumption:</strong> {assumed_return:.1f}% a year</p>
                    <p><strong>Personal target:</strong> {target_return:.1f}% a year</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if assumed_return >= target_return:
                st.success("The selected assumption meets or exceeds your target return.")
            else:
                st.warning("The selected assumption is below your target return.")

        projection_metrics = st.columns(3)
        projection_metrics[0].metric(
            "Projected value",
            f"£{projected_value:,.2f}",
            help="Estimated future value after compound growth and monthly contributions, using your selected assumptions.",
        )
        projection_metrics[1].metric(
            "Estimated gain",
            f"£{estimated_gain:,.2f}",
            help="Projected value minus the current portfolio and all future cash contributions.",
        )
        projection_metrics[2].metric(
            "Total contributed",
            f"£{total_contributed:,.2f}",
            help="Current portfolio value plus all monthly contributions; this excludes investment growth.",
        )

        projection_rows = []
        low_rate = assumed_rate - 0.03
        high_rate = assumed_rate + 0.03
        for year in range(0, projection_years + 1):
            projection_rows.extend(
                [
                    {"Year": year, "Scenario": "Lower", "Value": project_future_value(total, low_rate, year, monthly_contribution)},
                    {"Year": year, "Scenario": "Selected", "Value": project_future_value(total, assumed_rate, year, monthly_contribution)},
                    {"Year": year, "Scenario": "Higher", "Value": project_future_value(total, high_rate, year, monthly_contribution)},
                ]
            )
        projection_frame = pd.DataFrame(projection_rows)
        projection_figure = px.line(
            projection_frame,
            x="Year",
            y="Value",
            color="Scenario",
            title="Illustrative portfolio value over time",
            color_discrete_map={"Lower": "#747b82", "Selected": "#f2f4f5", "Higher": "#aeb4ba"},
        )
        projection_figure.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            yaxis_tickprefix="£",
            legend_title_text="Annual-return scenario",
        )
        projection_figure.update_xaxes(showgrid=False, dtick=max(1, projection_years // 10))
        st.plotly_chart(projection_figure, use_container_width=True)
        st.caption(
            "Illustration only—not financial advice. Lower and higher scenarios are three percentage points below and above your selected annual return. Actual returns can vary substantially and losses are possible."
        )

with simulation_tab:
    st.subheader("Stock simulation")
    try:
        clean_ticker = simulation_ticker.strip().upper()
        sim_prices = download_prices([clean_ticker], period="2y")
        sim_price_df = sim_prices.get(clean_ticker)
        if sim_price_df is None or sim_price_df.empty:
            st.info("No price history was returned for that ticker yet.")
        else:
            sim_result = simulate_from_prices(
                sim_price_df,
                investment_amount=float(simulation_amount),
                horizon_years=int(simulation_horizon),
            )
            sim_columns = st.columns(3)
            sim_columns[0].metric("Ticker", clean_ticker)
            sim_columns[1].metric("Projected value", f"£{sim_result['projected_value']:,.2f}")
            sim_columns[2].metric("Annualized return", f"{sim_result['annualized_return'] * 100:.2f}%")
            st.caption(
                f"Starting price: {sim_result['start_price']:.2f} — "
                f"Ending price: {sim_result['end_price']:.2f}"
            )
    except Exception as exc:
        st.warning(f"Simulation unavailable: {exc}")

with risk_tab:
    st.subheader("Risk profile")
    risk_control_column, risk_result_column = st.columns([1.2, 0.8], gap="large")
    with risk_control_column:
        risk_tolerance = st.slider("Risk tolerance", 1, 5, 3)
        investment_horizon = st.slider("Investment horizon (years)", 1, 10, 5)
        volatility = st.slider("Estimated volatility", 0.05, 0.60, 0.25, step=0.01)
    profile = evaluate_risk_profile(risk_tolerance, investment_horizon, volatility)
    with risk_result_column:
        st.markdown(
            f"""
            <div class="profile-card">
                <p><strong>Suggested profile:</strong> {profile['label']}</p>
                <p><strong>Time horizon:</strong> {profile['horizon_label']}</p>
                <p><strong>Risk level:</strong> {profile['risk_level']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

with performance_tab:
    st.subheader("Performance examples")
    for ticker in tickers:
        price_frame = prices.get(ticker)
        if price_frame is None or price_frame.empty:
            st.write(f"No data for {ticker}")
            continue
        ticker_returns = daily_returns_from_prices(price_frame)
        volatility_value = portfolio_volatility(ticker_returns)
        sharpe_value = sharpe_ratio(ticker_returns)
        st.write(f"**{ticker}** — Volatility: {volatility_value:.2%}, Sharpe: {sharpe_value:.2f}")
        performance_figure = px.line(
            price_frame,
            y="Close",
            title=f"{ticker} price history",
            color_discrete_sequence=[LSEG_COLORS[0]],
        )
        performance_figure.update_layout(
            margin=dict(l=20, r=20, t=55, b=20),
            xaxis_title=None,
            yaxis_title="Close",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        performance_figure.update_xaxes(showgrid=False)
        st.plotly_chart(performance_figure, use_container_width=True)

with ai_tab:
    st.subheader("AI Portfolio Assistant")

    if "ai_messages" not in st.session_state:
        summary = get_portfolio_summary(df_vals, total, portfolio_return, historical_performance, tickers)
        st.session_state.ai_messages = [
            {"role": "system", "content": build_system_prompt(summary)},
            {"role": "assistant", "content": "I can answer questions about your portfolio. Try asking about your top holding, performance, risk, or diversification."},
        ]

    chat_history = [m for m in st.session_state.ai_messages if m["role"] != "system"]

    for msg in chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about your portfolio..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.ai_messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                reply = chat(st.session_state.ai_messages)
            st.markdown(reply)
            st.session_state.ai_messages.append({"role": "assistant", "content": reply})

st.divider()
holdings_column, allocation_column = st.columns([1.18, 0.82], gap="large")
with holdings_column:
    st.markdown('<div class="section-kicker">Positions</div>', unsafe_allow_html=True)
    st.subheader("Holdings")
    ordered_holdings = df_vals.sort_values("Value", ascending=False)
    st.dataframe(number_rows_from_one(ordered_holdings), use_container_width=True)

with allocation_column:
    st.markdown('<div class="section-kicker">Exposure</div>', unsafe_allow_html=True)
    st.subheader("Allocation")
    allocation_figure = px.pie(
        df_vals,
        names="Ticker",
        values="Value",
        title="Portfolio allocation by holding",
        hole=0.48,
        color_discrete_sequence=LSEG_COLORS,
    )
    allocation_figure.update_traces(textposition="inside", textinfo="percent+label")
    allocation_figure.update_layout(
        margin=dict(l=20, r=20, t=55, b=20),
        legend_title_text="Holding",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(allocation_figure, use_container_width=True)
