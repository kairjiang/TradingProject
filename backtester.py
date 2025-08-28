import yfinance as yf
import datetime as dt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- Configuration ---
STOCK_SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']
BENCHMARK_SYMBOL = 'SPY'  # S&P 500 ETF as the benchmark
RISK_FREE_SYMBOL = '^IRX'  # 13 Week Treasury Bill
START_DATE = dt.datetime(2010, 1, 1)
END_DATE = dt.datetime(2023, 12, 31)
MOVING_AVERAGE_WINDOW = 200

def download_data(symbols, start, end):
    """Downloads adjusted close prices from Yahoo Finance."""
    print("Downloading historical data...")
    # The yfinance library now defaults to auto_adjust=True, which places the
    # adjusted close price in the 'Close' column. We select that column.
    data = yf.download(symbols, start=start, end=end)
    return data['Close']

def calculate_strategy_returns(data):
    """Calculates returns for the 200-day moving average strategy."""
    daily_returns = data.pct_change().dropna()
    
    # Calculate 200-day moving averages
    ma200 = data.rolling(window=MOVING_AVERAGE_WINDOW).mean()

    # Determine positions: 1 if stock price > moving average, 0 otherwise
    # We shift the data by 1 day to ensure we trade on the next day's open
    positions = (data.shift(1) > ma200.shift(1)).astype(int)

    # Allocate portfolio: 20% to each stock or 0% if below moving average
    num_stocks = len(data.columns)
    portfolio_allocations = positions.multiply(1 / num_stocks)

    # Calculate portfolio returns
    # We shift allocations by 1 to ensure we are using yesterday's signal for today's returns
    strategy_returns = (portfolio_allocations.shift(1) * daily_returns).sum(axis=1)
    
    return strategy_returns

def calculate_benchmark_returns(data):
    """Calculates returns for the benchmark."""
    return data.pct_change().dropna()

def calculate_statistics(returns, risk_free_rate):
    """Calculates mean, standard deviation, and Sharpe Ratio."""
    mean_return = returns.mean() * 252  # Annualized
    std_dev = returns.std() * np.sqrt(252)  # Annualized
    
    # Calculate annualized risk-free rate
    annual_risk_free = (1 + risk_free_rate.mean())**252 - 1
    
    sharpe_ratio = (mean_return - annual_risk_free) / std_dev if std_dev != 0 else 0
    return mean_return, std_dev, sharpe_ratio

def plot_performance(strategy_cumulative, benchmark_cumulative, title):
    """Plots the cumulative performance of the strategy vs. the benchmark."""
    plt.figure(figsize=(12, 7))
    plt.plot(strategy_cumulative, label='Moving Average Strategy')
    plt.plot(benchmark_cumulative, label='S&P 500 (SPY) Benchmark')
    plt.legend()
    plt.title(title)
    plt.xlabel('Date')
    plt.ylabel('Cumulative Returns')
    plt.grid(True)
    plt.show()

def main():
    """Main function to run the backtest."""
    # Download data for stocks and benchmark
    stock_data = download_data(STOCK_SYMBOLS, start=START_DATE, end=END_DATE)
    benchmark_data = download_data(BENCHMARK_SYMBOL, start=START_DATE, end=END_DATE)
    risk_free_data = download_data(RISK_FREE_SYMBOL, start=START_DATE, end=END_DATE)
    
    # Convert risk-free rate to daily
    daily_risk_free = risk_free_data / (100 * 360)

    # Calculate returns
    strategy_returns = calculate_strategy_returns(stock_data)
    benchmark_returns = calculate_benchmark_returns(benchmark_data)

    # Align dataframes by date
    aligned_returns = pd.concat([strategy_returns, benchmark_returns, daily_risk_free], axis=1).dropna()
    aligned_returns.columns = ['Strategy', 'Benchmark', 'RiskFree']
    
    # Calculate cumulative returns
    cumulative_strategy = (1 + aligned_returns['Strategy']).cumprod()
    cumulative_benchmark = (1 + aligned_returns['Benchmark']).cumprod()

    # Calculate and print statistics
    strategy_mean, strategy_std, strategy_sharpe = calculate_statistics(aligned_returns['Strategy'], aligned_returns['RiskFree'])
    benchmark_mean, benchmark_std, benchmark_sharpe = calculate_statistics(aligned_returns['Benchmark'], aligned_returns['RiskFree'])

    print("\n--- Strategy Performance ---")
    print(f"Annualized Mean Return: {strategy_mean:.2%}")
    print(f"Annualized Std. Deviation: {strategy_std:.2%}")
    print(f"Annualized Sharpe Ratio: {strategy_sharpe:.2f}")

    print("\n--- S&P 500 Benchmark Performance ---")
    print(f"Annualized Mean Return: {benchmark_mean:.2%}")
    print(f"Annualized Std. Deviation: {benchmark_std:.2%}")
    print(f"Annualized Sharpe Ratio: {benchmark_sharpe:.2f}")

    # Plot results
    plot_performance(cumulative_strategy, cumulative_benchmark, 'Moving Average Strategy vs. S&P 500 Benchmark')

if __name__ == "__main__":
    main()