import sys

import yfinance as yf
import datetime as dt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# List of stock symbols
stock_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']
risk_free_symbol = '^IRX'

# Define the date range
start_date = dt.datetime(2010, 1, 1)
end_date = dt.datetime(2023, 12, 31)

data = yf.download(stock_symbols, start=start_date, end=end_date)['Adj Close']
risk_free = yf.download(risk_free_symbol, start=start_date, end=end_date)['Adj Close']

# Set display options to show all rows and columns
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

# Calculate daily returns
daily_returns = data.pct_change().ffill()
risk_free_daily_returns = risk_free.shift(1) / 36500

daily_cum = (1 + daily_returns).cumprod()
constant_allocation = 0

for symbol in stock_symbols:
    constant_allocation += daily_cum[symbol] * 0.2

# print(constant_allocation.iloc[-1])

# Align dimensions and compute excess returns
excess_returns = daily_returns.subtract(risk_free_daily_returns, axis=0)

# Calculate 200-day moving averages
MA200 = data.rolling(window=200).mean()

# Determine positions: 1 if stock price > moving average, 0 otherwise
positions = (data.shift(1) > MA200).astype(int)

# Allocate portfolio: 20% to stock or 0% if below moving average
portfolio_allocations = positions.multiply(0.2)

# Calculate portfolio returns: element-wise multiply and row-wise sum
portfolio_returns = (portfolio_allocations.shift(1) * daily_returns).sum(axis=1)

# Statistics
portfolio_mean = portfolio_returns.mean()
portfolio_std = portfolio_returns.std()
constant_mean = constant_allocation.mean()
constant_std = constant_allocation.std()

# Calculate cumulative returns
cumulative_constant = constant_allocation
cumulative_strategy = (1 + portfolio_returns).cumprod()

# Plotting
plt.figure(figsize=(10, 6))
plt.plot(cumulative_constant, label='Constant Allocation Strategy')
plt.plot(cumulative_strategy, label='Moving Average Strategy')
plt.legend()
plt.title('Cumulative Performance Comparison')
plt.xlabel('Date')
plt.ylabel('Cumulative Returns')
plt.show()
