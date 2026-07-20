# Mini LSEG Portfolio Analytics Terminal

Quick start for beginners.

Prerequisites
- Python 3.12+

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
.venv\Scripts\Activate.ps1 # Windows (PowerShell)
pip install -r requirements.txt
```

Run the app locally:

```bash
streamlit run app.py
```

If `yfinance` fails (network or rate limits), the app will show which tickers couldn't be downloaded.
