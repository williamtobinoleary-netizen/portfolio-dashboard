# LSEG Portfolio Analytics — Ground-Up Build Instructions

## 1. Product definition

Build a responsive Streamlit dashboard for creating or uploading a stock portfolio, retrieving market data, calculating portfolio analytics, viewing company and UK-market news, exploring projections, and asking a local AI assistant questions about the portfolio.

The application is an educational analytics tool. Forecasts and buy/hold/sell language must always be described as mechanical research indicators, not personalised financial advice or price targets.

## 2. Core user experience

The finished dashboard should let a user:

1. Build a portfolio from a predefined list of London-listed companies.
2. Upload a CSV containing `Ticker` and `Shares` columns.
3. Load a sample portfolio from `portfolio.csv`.
4. Select a price-history period and refresh market data.
5. View company price history, a short trend projection, and latest company news.
6. View a compact Sell–Hold–Buy research gauge derived from visible trend inputs.
7. Read a separate, short UK-market news brief.
8. See total value, total shares, top holding, concentration, and historical return.
9. Explore portfolio projections, stock simulation, risk profile, performance, and an AI assistant.
10. Review holdings and allocation after the analysis workspace.
11. Switch between Streamlit light, dark, and system themes without hard-coded colours breaking the page.

## 3. Recommended technology

- Python 3.12 or newer
- Streamlit for the application and controls
- pandas for tabular data
- NumPy for numerical calculations and trend fitting
- Plotly Express for interactive charts
- yfinance for historical prices and news
- llama.cpp with an OpenAI-compatible local endpoint for the optional AI assistant

Install the Python packages with:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`requirements.txt` should contain:

```text
pandas
numpy
yfinance
plotly
streamlit
```

Run the dashboard with:

```powershell
streamlit run app.py
```

## 4. Project structure

```text
portfolio-dashboard/
├── app.py                    # Streamlit layout and orchestration
├── portfolio.csv             # Sample Ticker,Shares portfolio
├── requirements.txt
├── test_smoke.py
└── utils/
    ├── portfolio.py          # Portfolio loading and Yahoo price retrieval
    ├── metrics.py            # Valuation, returns, risk, and projection maths
    ├── simulation.py         # Single-stock simulation and risk profile
    └── ai_assistant.py       # Optional local LLM client and portfolio prompt
```

Keep financial calculations in `utils` rather than embedding all logic in `app.py`. Keep Streamlit widgets, layout, styling, and session state in `app.py`.

## 5. Build sequence

### Phase 1 — Portfolio input

Create a loader that:

- accepts a file path or uploaded file;
- requires `Ticker` and `Shares`;
- strips ticker whitespace;
- converts shares to numeric values;
- removes empty tickers and invalid rows;
- aggregates duplicate tickers;
- returns a clean DataFrame.

Offer three sidebar sources: Build in app, Upload CSV, and Sample portfolio. The in-app builder should use a ticker-to-company-name dictionary and create one share input per selected company.

### Phase 2 — Market data

Use `yfinance.download` for efficient multi-ticker historical downloads. Return a dictionary mapping every requested ticker to a DataFrame containing `Close`. If a batch request fails, fall back to per-ticker history requests and return an empty DataFrame for unavailable symbols.

Yahoo generally reports London `.L` quotes in GBp. Divide the latest `.L` quote by 100 before calculating GBP portfolio values. Keep historical company charts labelled as GBp unless their complete historical series is also converted.

Handle missing, empty, delayed, and partially available data without crashing the page.

### Phase 3 — Portfolio calculations

Implement and test:

- position value: `latest_price × shares`;
- total value: sum of valid position values;
- holding weight: `position_value / total_value`;
- daily return: percentage change in close;
- annualised volatility: `daily_std × sqrt(252)`;
- Sharpe ratio using daily excess return and `sqrt(252)`;
- portfolio historical return using current share quantities at period start and end;
- annualised return based on actual elapsed days;
- future value with monthly compounding and end-of-month contributions.

Historical results must state that they exclude fees, tax, dividends, inflation, and currency effects.

### Phase 4 — Market-intelligence workspace

Place this immediately below a compact title strip. Use a wide left column and narrower right column.

The right column should contain:

- a selector covering every supported company;
- a latest-company-news feed;
- linked headline, provider, and publication time;
- a friendly empty state when news is unavailable.

The left column should contain:

- latest close;
- a historical price chart;
- a 30-trading-day linear trend illustration;
- a compact research signal;
- a separately styled UK-market brief.

Cache news for approximately 15 minutes to limit repeated Yahoo requests. Normalise both legacy and current yfinance news payloads. Only render HTTP or HTTPS links, and HTML-escape external titles, publishers, and URLs.

For the UK brief, request FTSE-related news, show no more than three headline-only items, and truncate unusually long titles. Visually separate this brief from the selected-company feed.

### Phase 5 — Forecast and signal

Build the trend illustration from up to 90 recent closes:

1. Require at least 10 valid observations.
2. Fit a first-degree NumPy polynomial to sequential trading-day positions.
3. Extend it across 30 future business days.
4. Clamp projected prices at zero.
5. Draw historical prices as a solid line and the projected trend as a dashed line.

Create the research signal from two visible inputs:

- 20-trading-day price momentum;
- percentage change between the latest close and final projected value.

Award `+1` when an input exceeds `+2%`, `-1` when it is below `-2%`, and zero otherwise. The combined score maps to:

- `+2`: Buy side of the gauge;
- `-2`: Sell side of the gauge;
- all other scores: Hold at the centre.

Render one fixed, non-interactive gradient gauge labelled Sell, Hold, and Buy. Add a high-contrast vertical line and pointer at approximately 12%, 50%, or 88%. Do not use large metric cards for this signal. Keep the explanation and input percentages compact.

Always state that this is a mechanical trend indicator, not personalised advice or a price target.

### Phase 6 — Portfolio overview and analysis

Show summary metrics for:

- total portfolio value;
- total shares;
- largest holding;
- largest holding weight;
- selected-period portfolio return.

Place the tabbed analysis workspace before the final Holdings and Allocation section. Include:

1. Portfolio projection with adjustable horizon, assumed return, monthly contribution, and target return.
2. Stock simulation with ticker, investment amount, and horizon.
3. Risk profile using tolerance, horizon, and estimated volatility.
4. Per-holding volatility, Sharpe ratio, and price charts.
5. Optional AI portfolio assistant.

Finish the page with a sorted holdings table and allocation doughnut chart.

### Phase 7 — Optional local AI assistant

Connect to a local OpenAI-compatible llama.cpp endpoint such as:

```text
http://127.0.0.1:8080/v1/chat/completions
```

The system prompt should receive a concise current-portfolio summary and instruct the model to use plain language, remain educational, and avoid presenting itself as a financial adviser.

Keep conversation history in `st.session_state`. Handle unavailable servers, timeouts, malformed responses, and HTTP errors with useful messages. The rest of the dashboard must work without the AI server.

## 6. Layout and theme requirements

- Use `layout="wide"` and an expanded sidebar.
- Keep the title card short so the market-intelligence area is visible immediately.
- Use a wide graph/forecast column and a narrower company-news column.
- Keep signal and news typography compact enough for laptop screens.
- Avoid fixed dark backgrounds and fixed light text.
- Base custom CSS on Streamlit variables including:
  - `--background-color`
  - `--secondary-background-color`
  - `--text-color`
  - `--primary-color`
- Let Plotly inherit the active Streamlit theme; do not force dark plot backgrounds or white chart fonts.
- Test Light, Dark, and System modes after every major styling change.

## 7. Reliability and security rules

- Validate uploaded schemas before calculations.
- Never trust titles or URLs received from a news service; escape content and restrict URL schemes.
- Cache external calls but give users a refresh path.
- Do not assume every ticker has prices or news.
- Avoid downloading the complete company universe on every rerun; fetch the active portfolio and selected intelligence ticker.
- Use explicit units: GBP for portfolio values and GBp for unconverted London price histories.
- Never describe a linear trend as a predictive model with proven accuracy.
- Preserve the dashboard when the optional AI service is offline.

## 8. Testing plan

Unit-test the utility functions with local DataFrames so most tests do not require network access:

- duplicate tickers are aggregated;
- malformed shares are handled;
- displayed row numbers start at one;
- latest prices map correctly;
- London pence conversion is correct;
- position values and totals are correct;
- historical return and CAGR are correct;
- zero-rate and non-zero-rate projections are correct;
- volatility and Sharpe calculations handle empty or constant returns;
- trend forecasts require sufficient observations and produce 30 business-day rows;
- signal thresholds map to Sell, Hold, and Buy correctly;
- news normalisation supports both payload formats and rejects unsafe URLs.

Add a separate optional integration test for live Yahoo requests. Do not make the core test suite depend on market availability.

Before handoff, run:

```powershell
python -m py_compile app.py utils\portfolio.py utils\metrics.py utils\simulation.py utils\ai_assistant.py
python -m pytest -q
streamlit run app.py
```

Then manually verify portfolio building, CSV upload, company switching, news links, projection controls, the research-gauge position, responsive layout, and all three theme choices.

## 9. Definition of done

The application is ready when:

- a new user can build or upload a portfolio without editing code;
- unavailable market data produces a useful empty state rather than an exception;
- all calculations show correct currency and percentage units;
- company news and the UK brief are visually distinct;
- the signal line visibly moves between Sell, Hold, and Buy based on documented inputs;
- portfolio analysis appears before holdings and allocation;
- light and dark modes style the complete interface;
- financial limitations are visible near projections and signals;
- core calculations pass offline automated tests;
- the app launches from a clean virtual environment using only the documented setup steps.
