# Moving Average Trading Strategy: Backtester & IBKR Bot
This project provides a framework for backtesting and deploying a simple quantitative trading strategy based on the 200-day simple moving average (SMA). It consists of two main components:

1. A backtesting script (`backtester.py`) that uses historical data from Yahoo Finance to evaluate the strategy's performance against a benchmark.

2. A live trading bot (`trading_bot.py`) that connects to the Interactive Brokers (IBKR) API to execute trades based on the same strategy in a paper or live account.

# The Strategy
The core logic is a classic trend-following strategy designed to hold assets during uptrends and exit them during downtrends.

- Buy/Hold Signal: A stock's position is initiated or held if its last closing price is above its 200-day moving average.

- Sell/Exit Signal: Any existing position in a stock is sold if its last closing price falls below its 200-day moving average.

The portfolio is equally weighted. For the 5 stocks in the list, the strategy allocates 20% of the portfolio to each stock that meets the "Buy/Hold" criteria. If a stock does not meet the criteria, its 20% allocation is effectively held as cash (i.e., not invested).

# Project Components

1. `backtester.py`

This script is responsible for evaluating the strategy's historical performance.

- Data Source: Downloads historical daily stock prices from Yahoo Finance (`yfinance`).

- Functionality:

  - Calculates daily returns for a predefined list of stocks.

  - Implements the 200-day SMA strategy and calculates the resulting portfolio returns.

  - Compares the strategy's performance against a "Constant Allocation" (i.e., buy-and-hold) benchmark.

  - Prints summary statistics (mean, standard deviation) for both strategies.

  - Generates a Matplotlib chart visualizing the cumulative returns over time.

2. `trading_bot.py`

This script connects to the Interactive Brokers API to execute the strategy in real-time.

- Framework: Uses the official Interactive Brokers Python API (`ibapi`).

- Functionality:

  - Connects to an instance of Trader Workstation (TWS) or IB Gateway.
  
  - Requests the last year of historical data for each stock to calculate the 200-day SMA.
  
  - Determines the current position (Buy or Sell) based on the latest closing price relative to the SMA.
  
  - Places Market Orders (`MKT`) to buy stocks that are above their SMA and sell owned stocks that have fallen below their SMA.
  
  - Keeps track of owned stocks to manage sell orders correctly.
