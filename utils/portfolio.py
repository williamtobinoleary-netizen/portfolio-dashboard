import pandas as pd

def load_portfolio(path="portfolio.csv"):
    """Load portfolio CSV with columns Ticker,Shares into a DataFrame."""
    df = pd.read_csv(path)
    df = df.dropna()
    df['Shares'] = df['Shares'].astype(float)
    return df

def download_prices(tickers, period="1y"):
    """Download historical Close prices for a list of tickers using yfinance.

    Returns a dict mapping ticker -> DataFrame with a `Close` column.
    """
    try:
        import yfinance as yf
    except Exception:
        raise RuntimeError("yfinance is required to download market data")

    data = {}
    # Use yf.download for multiple tickers for efficiency
    try:
        tickers_str = " ".join(tickers)
        raw = yf.download(tickers_str, period=period, group_by='ticker', threads=True, progress=False)
        if len(tickers) == 1:
            data[tickers[0]] = raw[['Close']].dropna()
            return data
        for t in tickers:
            try:
                df = raw[t][['Close']].dropna()
            except Exception:
                df = yf.Ticker(t).history(period=period)[['Close']].dropna()
            data[t] = df
        return data
    except Exception:
        # Fallback: fetch per-ticker
        for t in tickers:
            try:
                df = yf.Ticker(t).history(period=period)[['Close']].dropna()
            except Exception:
                df = pd.DataFrame()
            data[t] = df
        return data

def get_latest_prices(price_dict):
    """Return a mapping ticker -> latest close price (or None)."""
    latest = {}
    for t, df in price_dict.items():
        if df is None or df.empty:
            latest[t] = None
        else:
            latest[t] = df['Close'].iloc[-1]
    return latest
