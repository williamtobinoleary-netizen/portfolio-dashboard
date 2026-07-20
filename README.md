# Mini LSEG Portfolio Analytics Terminal

A simple portfolio analytics dashboard built with Python, Streamlit and Plotly.

## What this project does

This app reads a portfolio from a CSV file, downloads recent market data, and shows:
- the total portfolio value
- the total number of shares held
- a holdings table with prices and values
- an allocation pie chart
- basic performance metrics for each ticker

It is designed as a beginner-friendly project for learning Python, pandas, financial calculations and simple web dashboards.

## Prerequisites

- Python 3.12+
- Git
- A terminal such as PowerShell or Command Prompt

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Run the app

```bash
streamlit run app.py
```

Then open the local URL shown in the terminal, usually http://localhost:8501/.

## Portfolio file

The app reads [portfolio.csv](portfolio.csv) by default, but you can also upload your own CSV through the sidebar to test different portfolios.

## Notes

If market data cannot be downloaded, the app will still show the portfolio data and indicate which tickers had no price history.
