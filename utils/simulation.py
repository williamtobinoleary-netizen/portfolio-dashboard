import pandas as pd
import numpy as np


def simulate_from_prices(price_df, investment_amount=1000, horizon_years=1):
    """Estimate a simple future value and return using historical price growth."""
    if price_df is None or price_df.empty or 'Close' not in price_df.columns:
        raise ValueError("price_df must contain a 'Close' column")

    closes = pd.to_numeric(price_df['Close'], errors='coerce').dropna()
    if len(closes) < 2:
        raise ValueError("Need at least two price points for a simulation")

    start = float(closes.iloc[0])
    end = float(closes.iloc[-1])
    total_return = (end / start - 1) if start else 0.0
    annualized_return = ((1 + total_return) ** (1 / max(horizon_years, 1)) - 1) if horizon_years else total_return
    projected_value = investment_amount * (1 + annualized_return)

    return {
        'start_price': start,
        'end_price': end,
        'total_return': total_return,
        'annualized_return': annualized_return,
        'projected_value': projected_value,
        'horizon_years': horizon_years,
    }


def evaluate_risk_profile(risk_tolerance, investment_horizon_years, volatility):
    """Map a simple risk profile from user preferences and volatility."""
    if risk_tolerance <= 2:
        label = 'Conservative'
    elif risk_tolerance <= 4:
        label = 'Balanced'
    else:
        label = 'Aggressive'

    if investment_horizon_years <= 2:
        horizon_label = 'Short-term'
    elif investment_horizon_years <= 5:
        horizon_label = 'Medium-term'
    else:
        horizon_label = 'Long-term'

    if volatility > 0.35:
        risk_level = 'High'
    elif volatility > 0.2:
        risk_level = 'Medium'
    else:
        risk_level = 'Low'

    return {
        'label': label,
        'horizon_label': horizon_label,
        'risk_level': risk_level,
        'volatility': volatility,
    }
