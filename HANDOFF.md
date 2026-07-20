# Portfolio Dashboard Handoff

## Project summary
This project is a Streamlit-based portfolio analytics dashboard for tracking a simple stock portfolio, downloading market data, calculating portfolio metrics, and running a basic stock simulation.

## Current structure
- app.py — main Streamlit dashboard entry point
- utils/portfolio.py — portfolio loading and market-data helper functions
- utils/metrics.py — portfolio metrics calculations
- utils/simulation.py — simple stock simulation and risk-profile helpers
- portfolio.csv — sample portfolio input
- test_smoke.py — basic regression/smoke checks
- requirements.txt — project dependencies

## What is already implemented
- Portfolio loading from a local CSV file
- CSV upload support in the dashboard
- Market data download from Yahoo Finance via yfinance
- Summary metrics such as:
  - total portfolio value
  - total shares
  - top holding
  - top holding weight
  - portfolio return
- Holdings table sorted by value from highest to lowest
- Allocation pie chart
- Performance examples for each ticker
- A simple stock simulation panel with:
  - ticker input
  - investment amount
  - horizon in years
  - projected value and annualized return
- A risk profile panel with sliders for:
  - risk tolerance
  - investment horizon
  - estimated volatility

## Important implementation notes
- The app uses Streamlit and Plotly.
- Market data comes from Yahoo Finance through yfinance.
- The dashboard expects a CSV with at least two columns:
  - Ticker
  - Shares
- The portfolio loader cleans the data, converts share values to numeric form, removes empty rows, and aggregates duplicate tickers.

## How to run locally
From the project folder:

1. Create and activate a virtual environment
2. Install dependencies:
   pip install -r requirements.txt
3. Start the app:
   streamlit run app.py

## Notes for the next person
- The app is currently functional and can be improved further with:
  - richer simulation charts
  - benchmark comparisons
  - more detailed risk scoring
  - better styling and formatting
- The numbering on displayed tables starts from 1.
- The dashboard title is "LSEG Portfolio Analytics".

## Files to review first
- app.py
- utils/portfolio.py
- utils/metrics.py
- utils/simulation.py
