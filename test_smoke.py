import io
import traceback
import pandas as pd
from utils.portfolio import load_portfolio, load_portfolio_from_upload, download_prices, get_latest_prices, number_rows_from_one
from utils.metrics import position_values, portfolio_historical_performance, project_future_value
from utils.simulation import simulate_from_prices, evaluate_risk_profile


def test_duplicate_tickers_are_aggregated():
    df = load_portfolio("portfolio.csv")
    assert 'TSLA' in df['Ticker'].tolist()
    assert df.loc[df['Ticker'] == 'TSLA', 'Shares'].iloc[0] == 12.0


def test_uploaded_csv_is_aggregated_and_cleaned():
    uploaded = io.StringIO("Ticker,Shares\nAAPL,2\nAAPL,3\nMSFT,5\n")
    df = load_portfolio_from_upload(uploaded)
    assert 'AAPL' in df['Ticker'].tolist()
    assert df.loc[df['Ticker'] == 'AAPL', 'Shares'].iloc[0] == 5.0
    assert 'MSFT' in df['Ticker'].tolist()


def test_number_rows_starts_at_one():
    df = load_portfolio("portfolio.csv")
    numbered = number_rows_from_one(df)
    assert numbered.index.tolist() == list(range(1, len(numbered) + 1))


def test_simulation_and_risk_profile_helpers():
    price_df = pd.DataFrame({
        'Close': [100, 102, 101, 105, 107, 110]
    })
    result = simulate_from_prices(price_df, investment_amount=1000, horizon_years=1)
    assert result['projected_value'] > 1000
    assert result['annualized_return'] > 0

    profile = evaluate_risk_profile(risk_tolerance=4, investment_horizon_years=5, volatility=0.25)
    assert profile['label'] in {'Conservative', 'Balanced', 'Aggressive'}


def test_portfolio_return_and_projection_helpers():
    portfolio = pd.DataFrame({'Ticker': ['AAA', 'BBB'], 'Shares': [2, 1]})
    dates = pd.to_datetime(['2025-01-01', '2026-01-01'])
    prices = {
        'AAA': pd.DataFrame({'Close': [100.0, 110.0]}, index=dates),
        'BBB': pd.DataFrame({'Close': [200.0, 220.0]}, index=dates),
    }
    performance = portfolio_historical_performance(portfolio, prices)
    assert round(performance['total_return'], 6) == 0.1
    assert round(performance['annualized_return'], 2) == 0.1
    assert round(project_future_value(1000, 0.10, 1), 2) == 1100.00
    assert project_future_value(1000, 0.0, 1, 100) == 2200


def run_smoke():
    try:
        print("Loading portfolio.csv...")
        df = load_portfolio("portfolio.csv")
        print("Loaded rows:", len(df))

        tickers = df['Ticker'].tolist()[:3]
        print("Test tickers:", tickers)

        print("Downloading recent prices (1mo)...")
        prices = download_prices(tickers, period="1mo")
        latest = get_latest_prices(prices)
        print("Latest prices:")
        for t in tickers:
            print(f"  {t}: {latest.get(t)}")

        df_vals, total = position_values(df, latest)
        print(f"Computed total value (approx): {total}")
        print("Smoke test completed successfully.")
    except Exception as e:
        print("Smoke test failed:")
        traceback.print_exc()


if __name__ == '__main__':
    test_duplicate_tickers_are_aggregated()
    test_uploaded_csv_is_aggregated_and_cleaned()
    run_smoke()
