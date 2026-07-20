import numpy as np

def position_values(portfolio_df, latest_prices):
    """Add `Price` and `Value` columns to portfolio_df and return total value."""
    df = portfolio_df.copy()
    df['Price'] = df['Ticker'].map(latest_prices)
    df['Value'] = df['Price'] * df['Shares']
    total = df['Value'].sum()
    return df, total

def daily_returns_from_prices(price_df):
    """Return daily percentage returns for a price DataFrame with `Close`."""
    return price_df['Close'].pct_change().dropna()

def portfolio_volatility(daily_returns):
    return daily_returns.std() * np.sqrt(252)

def sharpe_ratio(daily_returns, risk_free_rate=0.0):
    avg_daily = daily_returns.mean()
    std_daily = daily_returns.std()
    if std_daily == 0:
        return float('nan')
    excess = avg_daily - (risk_free_rate / 252)
    return (excess / std_daily) * np.sqrt(252)
