import traceback
from utils.portfolio import load_portfolio, download_prices, get_latest_prices
from utils.metrics import position_values


def test_duplicate_tickers_are_aggregated():
    df = load_portfolio("portfolio.csv")
    assert 'TSLA' in df['Ticker'].tolist()
    assert df.loc[df['Ticker'] == 'TSLA', 'Shares'].iloc[0] == 12.0


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
    run_smoke()
