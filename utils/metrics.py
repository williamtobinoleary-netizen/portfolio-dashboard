import numpy as np
import pandas as pd


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


def portfolio_return_from_prices(price_dict):
    """Return total return percentage for each ticker using the first and last close prices."""
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


def portfolio_historical_performance(portfolio_df, price_dict):
    """Estimate buy-and-hold performance for the complete portfolio.

    The calculation assumes the current share quantities were held for the
    selected price-history period and excludes fees, taxes, dividends, and
    currency conversion.
    """
    shares_by_ticker = portfolio_df.set_index('Ticker')['Shares'].to_dict()
    start_value = 0.0
    end_value = 0.0
    first_dates = []
    last_dates = []

    for ticker, shares in shares_by_ticker.items():
        frame = price_dict.get(ticker)
        if frame is None or frame.empty or 'Close' not in frame.columns:
            continue
        closes = pd.to_numeric(frame['Close'], errors='coerce').dropna()
        if len(closes) < 2:
            continue
        start_value += float(shares) * float(closes.iloc[0])
        end_value += float(shares) * float(closes.iloc[-1])
        first_dates.append(pd.Timestamp(closes.index[0]))
        last_dates.append(pd.Timestamp(closes.index[-1]))

    if start_value <= 0 or not first_dates or not last_dates:
        return None

    total_return = end_value / start_value - 1
    elapsed_days = max((max(last_dates) - min(first_dates)).days, 1)
    elapsed_years = elapsed_days / 365.25
    annualized_return = (end_value / start_value) ** (1 / elapsed_years) - 1
    return {
        'start_value': start_value,
        'end_value': end_value,
        'total_return': total_return,
        'annualized_return': annualized_return,
        'elapsed_years': elapsed_years,
    }


def project_future_value(current_value, annual_rate, years, monthly_contribution=0.0):
    """Project compound growth with contributions made at each month end."""
    months = max(int(years * 12), 0)
    if annual_rate <= -1:
        raise ValueError("annual_rate must be greater than -100%")
    monthly_rate = (1 + annual_rate) ** (1 / 12) - 1
    grown_portfolio = float(current_value) * (1 + monthly_rate) ** months
    if monthly_rate == 0:
        grown_contributions = float(monthly_contribution) * months
    else:
        grown_contributions = float(monthly_contribution) * (
            ((1 + monthly_rate) ** months - 1) / monthly_rate
        )
    return grown_portfolio + grown_contributions
