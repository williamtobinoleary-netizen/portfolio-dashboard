# Mini LSEG Portfolio Analytics Terminal

## Overview

This project guides a finance student (or beginner Python user) through building a simple portfolio analytics dashboard. The goals are to learn practical Python, data analysis, visualization and basic software engineering while delivering a working Streamlit dashboard.

By the end you will have an app that:
- Imports a portfolio from a CSV
- Fetches market data
- Calculates performance and risk metrics
- Visualises portfolio composition and performance
- Displays results in a web dashboard
- Uses GitHub and GitHub Copilot during development

Work through the steps in order. Each step builds on the previous one.

## Learning Objectives

### Python
- Variables, lists, dictionaries
- Loops, functions, error handling
- Working with external libraries

### Data Analysis
- Pandas DataFrames, cleaning, aggregations
- Financial calculations (returns, cumulative performance)

### Visualisation
- Interactive Plotly charts
- Embedding charts in Streamlit

### Software Engineering
- VS Code, Git and GitHub
- Repository structure and documentation
- Using GitHub Copilot as an assistant

## Final Deliverable

A web-based Portfolio Analytics Dashboard showing:
- Portfolio summary (value, return, volatility, Sharpe)
- Portfolio allocation pie chart
- Performance over time
- Individual stock performance
- Daily return distribution

## Project Structure

Example layout:

```
portfolio-dashboard/
├── app.py
├── portfolio.csv
├── requirements.txt
├── README.md
├── data/
├── charts/
└── utils/
    ├── portfolio.py
    └── metrics.py
```

## Prerequisites

Install:

- Python 3.12+
- VS Code
- Git and a GitHub account
- (Optional) GitHub Copilot

## Required Python Packages

Install via pip:

```bash
pip install pandas numpy yfinance plotly streamlit
```

Or create `requirements.txt` with:

```
pandas
numpy
yfinance
plotly
streamlit
```

Install everything:

```bash
pip install -r requirements.txt
```

## Sample portfolio file

Create `portfolio.csv` with the columns `Ticker,Shares`.

```csv
Ticker,Shares
MSFT,10
AAPL,15
NVDA,5
LSEG.L,20
AMZN,8
```

## Build Steps

Follow these steps. Verify each step before moving on.

### Step 1 — Set up the project

```bash
mkdir portfolio-dashboard
cd portfolio-dashboard
git init
```

Create the repo on GitHub and push your initial commit:

```bash
git add .
git commit -m "Initial project setup"
git remote add origin https://github.com/<your-username>/portfolio-dashboard.git
git branch -M main
git push -u origin main
```

### Step 2 — Learn Python basics

Practice small snippets (variables, lists, dicts, loops, functions) and simple tasks like summing shares and computing position values.

### Step 3 — Load data with Pandas

```python
import pandas as pd
df = pd.read_csv("portfolio.csv")
df.head()
```

### Step 4 — Download market data

Use `yfinance` to fetch historical prices for each ticker and store them in DataFrames.

```python
import yfinance as yf
t = yf.Ticker("MSFT")
prices = t.history(period="1y")
```

### Step 5 — Calculate portfolio value & performance

- Get latest prices and compute position values
- Sum to get total portfolio value
- Compute returns (daily and total)

Example:

```python
latest_price = prices["Close"].iloc[-1]
position_value = latest_price * shares
daily_returns = prices["Close"].pct_change()
total_return = prices["Close"].iloc[-1] / prices["Close"].iloc[0] - 1
```

### Step 6 — Risk metrics

Compute volatility and Sharpe ratio:

```python
import numpy as np
volatility = daily_returns.std() * np.sqrt(252)
avg_daily = daily_returns.mean()
sharpe = (avg_daily / daily_returns.std()) * np.sqrt(252)
```

### Step 7 — Build charts

Use Plotly for:
- Allocation pie chart
- Performance over time
- Individual stock comparison
- Daily return histogram

### Step 8 — Organise code

Move reusable logic into `utils/portfolio.py` and `utils/metrics.py` and keep `app.py` focused on presentation.

### Step 9 — Streamlit dashboard

Basic structure (`app.py`):

```python
import streamlit as st
st.title("Mini LSEG Portfolio Analytics Terminal")
# Load data, compute metrics, show numbers and charts
```

Run locally:

```bash
streamlit run app.py
```

### Step 10 — Document and share

- Write a clear `README.md` explaining how to run and what the project does
- Commit and push your work frequently

## Stretch Goals (optional)

- Allow CSV upload in the dashboard
- Add more risk metrics (e.g. max drawdown)
- Compare to a benchmark index
- Add date-range filters and improved styling

## Key Takeaways

- Push work regularly and maintain a clear commit history
- Use the project as a portfolio piece and link it on your CV/LinkedIn
- Be ready to explain how each part works and how Copilot assisted

Mini LSEG Portfolio Analytics Terminal
Overview
This project is designed for a Finance student with little or no Python experience.
The goal is to build a simple portfolio analytics dashboard using modern developer tools and AI assistance, while learning key software engineering principles.
By the end of the project, you will have built a working application that:
•	Imports a portfolio from a CSV file
•	Fetches market data
•	Calculates portfolio performance
•	Calculates risk metrics
•	Visualises portfolio composition
•	Displays results in a web dashboard
•	Uses GitHub Copilot as a development assistant
Work through the steps in order. Each step builds on the previous one. There is no fixed schedule — take the time you need, and use GitHub Copilot to help you understand anything unfamiliar.
________________________________________
Learning Objectives
Python
•	Variables
•	Lists
•	Dictionaries
•	Loops
•	Functions
•	Error handling
•	Working with external libraries
Data Analysis
•	Pandas DataFrames
•	Data cleaning
•	Calculations and aggregations
•	Financial analysis
Visualisation
•	Plotly charts
•	Interactive dashboards
Software Engineering
•	VS Code
•	Git
•	GitHub
•	GitHub Copilot
•	Repository management
•	Documentation
________________________________________
Final Deliverable
A web-based Portfolio Analytics Dashboard.
Example outputs:
Portfolio Summary
Portfolio Value: £25,000

Portfolio Return: +8.4%

Volatility: 14.2%

Sharpe Ratio: 1.12
Portfolio Charts
•	Portfolio Allocation Pie Chart
•	Performance Over Time
•	Individual Stock Performance
•	Daily Return Distribution
________________________________________
Project Structure
portfolio-dashboard/
│
├── app.py
├── portfolio.csv
├── requirements.txt
├── README.md
│
├── data/
├── charts/
└── utils/
    ├── portfolio.py
    └── metrics.py
________________________________________
Prerequisites
Install:
•	Python 3.12+
•	VS Code
•	Git
•	GitHub Account
•	GitHub Copilot
________________________________________
Required Python Packages
Install dependencies:
pip install pandas
pip install numpy
pip install yfinance
pip install plotly
pip install streamlit
Or create a requirements.txt file:
pandas
numpy
yfinance
plotly
streamlit
Install:
pip install -r requirements.txt
________________________________________
Sample Portfolio File
Create a file called:
portfolio.csv
Contents:
Ticker,Shares
MSFT,10
AAPL,15
NVDA,5
LSEG.L,20
AMZN,8
________________________________________
Build Steps
Follow these steps in order. Don't rush — make sure each step works before moving on to the next one. Use GitHub Copilot to explain code, suggest fixes, and answer questions as you go.
Step 1 - Set Up Your Environment
Install Tools
•	Python
•	VS Code
•	Git
•	GitHub Copilot
Create a GitHub Account
If you don't already have one, create a free account at github.com. This is where your finished project will live so you can show it on your CV and LinkedIn. Pick a professional username — it becomes part of your public profile.
Create the Project
mkdir portfolio-dashboard
cd portfolio-dashboard
Initialise a Git Repository
git init
Make Your First Commit
git add .
git commit -m "Initial project setup"
Create the Repository on GitHub and Push
Create a new repository on GitHub, then connect it to your local project and push your first commit. Do this early so you can keep pushing your work as you go — every step you complete should be committed and pushed.
git remote add origin https://github.com/<your-username>/portfolio-dashboard.git
git branch -M main
git push -u origin main
Understand the Basics
•	What is Git?
•	What is GitHub?
•	What is a repository?
•	What is a commit?
•	What is a branch?
________________________________________
Step 2 - Learn Python Fundamentals
Variables
stock = "MSFT"
shares = 10
Lists
stocks = ["MSFT", "AAPL", "NVDA"]
Dictionaries
portfolio = {
    "MSFT": 10,
    "AAPL": 15
}
Loops
for stock in portfolio:
    print(stock)
Functions
def portfolio_value(price, quantity):
    return price * quantity
Practice
•	Calculate total shares
•	Find the largest holding
•	Calculate position values
________________________________________
Step 3 - Load Data with Pandas
Import Pandas
import pandas as pd
Read the CSV
df = pd.read_csv("portfolio.csv")
Explore the Data
df.head()
df.info()
Practice
•	Sum total shares
•	Sort by shares
•	Filter specific stocks
________________________________________
Step 4 - Download Market Data
Import yfinance
import yfinance as yf
Fetch Historical Prices
ticker = yf.Ticker("MSFT")

prices = ticker.history(period="1y")
Goals
•	Download data for all portfolio stocks
•	Store the data in DataFrames
•	Understand historical pricing data
________________________________________
Step 5 - Calculate Portfolio Value and Performance
Get the Latest Prices
For each stock in the portfolio, take the most recent closing price.
latest_price = prices["Close"].iloc[-1]
Calculate Position Values
position_value = latest_price * shares
Calculate Total Portfolio Value
Add up the value of every position to get the total portfolio value.
Calculate Returns
# Daily percentage change in price
daily_returns = prices["Close"].pct_change()

# Total return over the period
total_return = (prices["Close"].iloc[-1] / prices["Close"].iloc[0]) - 1
Goals
•	Work out the current value of each holding
•	Calculate the total portfolio value
•	Calculate the overall portfolio return
•	Store the results so they can be displayed later
________________________________________
Step 6 - Calculate Risk Metrics
Volatility
Volatility measures how much the returns move up and down. Higher volatility means more risk.
import numpy as np

# Annualised volatility from daily returns
volatility = daily_returns.std() * np.sqrt(252)
Sharpe Ratio
The Sharpe ratio compares return to risk. A higher number is better.
average_daily_return = daily_returns.mean()
sharpe_ratio = (average_daily_return / daily_returns.std()) * np.sqrt(252)
Goals
•	Calculate volatility for the portfolio
•	Calculate the Sharpe ratio
•	Understand what each number means in plain English
________________________________________
Step 7 - Build the Charts
Use Plotly to create interactive charts.
import plotly.express as px
Portfolio Allocation Pie Chart
Show how the portfolio is split across holdings by value.
Performance Over Time
Plot the total portfolio value over the past year.
Individual Stock Performance
Compare how each stock has performed.
Daily Return Distribution
Show the spread of daily returns as a histogram.
Goals
•	Create each of the four charts
•	Make sure the charts are clear and labelled
•	Test the charts with the sample portfolio
________________________________________
Step 8 - Organise the Code
Move reusable code into the utils/ folder to keep things tidy.
utils/
├── portfolio.py   # Loading the CSV, calculating values and returns
└── metrics.py     # Volatility, Sharpe ratio and other risk metrics
Goals
•	Move calculation functions into portfolio.py and metrics.py
•	Import these functions into the main app
•	Keep app.py focused on displaying results
________________________________________
Step 9 - Build the Web Dashboard
Use Streamlit to turn the code into a web app.
import streamlit as st
Basic Structure
st.title("Mini LSEG Portfolio Analytics Terminal")

st.header("Portfolio Summary")
# Show portfolio value, return, volatility and Sharpe ratio

st.header("Charts")
# Display the Plotly charts
Run the App
streamlit run app.py
Goals
•	Show the portfolio summary numbers at the top
•	Display all four charts on the page
•	Confirm the app runs locally in the browser
________________________________________
Step 10 - Document and Share Your Work
Write the README
Create a README.md that explains:
•	What the project does
•	How to install and run it
•	A short description of each feature
Commit and Push to GitHub
git add .
git commit -m "Complete portfolio analytics dashboard"
git push
Goals
•	Write clear documentation
•	Push the finished project to GitHub
•	Be able to explain how the app works and how Copilot helped
________________________________________
Stretch Goals (Optional)
If you finish early and want to go further:
•	Let the user upload their own portfolio CSV in the dashboard
•	Add more risk metrics (for example, maximum drawdown)
•	Compare the portfolio against a benchmark such as an index
•	Add date range filters to the charts
•	Improve the styling and layout of the dashboard
________________________________________
Key Takeaways
This project is more than a learning exercise — it is a piece of work you can show off. Make sure you get the following out of it:
•	Create a GitHub account. A free, professional GitHub profile is a standard expectation for anyone starting a career in tech or finance-tech.
•	Push your work as you go. Don't leave it until the end. Commit and push at every step so your GitHub shows a steady history of progress.
•	Build a public portfolio. A finished, public repository with a clear README proves you can build and ship something real.
•	Link it to your CV and LinkedIn. Add the repository URL to your CV and LinkedIn profile. A live project link is far more convincing than a bullet point.
•	Be able to talk about it. Understand what each part does so you can explain the project confidently in an interview, including how you used GitHub Copilot to help you build it.

