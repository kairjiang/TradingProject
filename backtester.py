import yfinance as yf
import datetime as dt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# --- Configuration ---
STOCK_SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']
BENCHMARK_SYMBOL = 'SPY'  # S&P 500 ETF as the benchmark
RISK_FREE_SYMBOL = '^IRX'  # 13 Week Treasury Bill
START_DATE = dt.datetime(2010, 1, 1)
END_DATE = dt.datetime(2023, 12, 31)
MOVING_AVERAGE_WINDOW = 200
CHART_OUTPUT_FOLDER = 'charts'

def download_data(symbols, start, end):
    """Downloads adjusted close prices from Yahoo Finance."""
    print("Downloading historical data...")
    data = yf.download(symbols, start=start, end=end)
    return data['Close']

def calculate_strategy_returns(data, ma_window):
    """Calculates returns for the moving average strategy."""
    daily_returns = data.pct_change().dropna()
    ma = data.rolling(window=ma_window).mean()
    positions = (data.shift(1) > ma.shift(1)).astype(int)
    num_stocks = len(data.columns) if isinstance(data, pd.DataFrame) else 1
    portfolio_allocations = positions.multiply(1 / num_stocks)
    strategy_returns = (portfolio_allocations.shift(1) * daily_returns).sum(axis=1)
    return strategy_returns, positions, ma

def calculate_benchmark_returns(data):
    """Calculates returns for the benchmark."""
    return data.pct_change().dropna()

def calculate_statistics(returns, risk_free_rate):
    """Calculates annualized mean return, standard deviation, and Sharpe Ratio."""
    mean_return = returns.mean() * 252
    std_dev = returns.std() * np.sqrt(252)
    annual_risk_free = (1 + risk_free_rate.mean())**252 - 1
    sharpe_ratio = (mean_return - annual_risk_free) / std_dev if std_dev != 0 else 0
    return mean_return, std_dev, sharpe_ratio

def plot_and_save_charts(strategy_cumulative, benchmark_cumulative, strategy_stats, benchmark_stats, stock_data, ma_data, positions, start_date, end_date):
    """Plots and saves a detailed multi-part performance chart for all stocks."""
    num_stocks = len(stock_data.columns)
    
    # --- Create a flexible grid for the plots ---
    # Calculate the number of rows needed for the stock charts in a 2-column layout
    stock_chart_rows = (num_stocks + 1) // 2
    
    # Create the figure. The total number of rows is 1 for the main chart + the stock chart rows.
    fig = plt.figure(figsize=(16, 8 + 4 * stock_chart_rows))
    fig.suptitle('Moving Average Strategy Analysis', fontsize=20)
    
    # Use GridSpec for a more flexible layout
    # The main chart will be taller than the individual stock charts
    gs = fig.add_gridspec(stock_chart_rows + 2, 2)

    # --- Plot 1: Cumulative Performance (spanning the full width) ---
    ax1 = fig.add_subplot(gs[0:2, :]) # Use first two rows, all columns
    ax1.plot(strategy_cumulative, label='Moving Average Strategy', color='royalblue', linewidth=2)
    ax1.plot(benchmark_cumulative, label='S&P 500 (SPY) Benchmark', color='darkorange', linewidth=2)
    ax1.set_title(f'Cumulative Returns ({start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")})', fontsize=14)
    ax1.set_ylabel('Cumulative Returns', fontsize=12)
    ax1.legend(loc='upper left', fontsize=10)
    ax1.grid(True, linestyle='--', alpha=0.6)

    # Add statistics box to the first plot
    stats_text = (
        f"--- Strategy Performance ---\n"
        f"Annualized Return: {strategy_stats[0]:.2%}\n"
        f"Annualized Std. Dev: {strategy_stats[1]:.2%}\n"
        f"Sharpe Ratio: {strategy_stats[2]:.2f}\n\n"
        f"--- S&P 500 Benchmark ---\n"
        f"Annualized Return: {benchmark_stats[0]:.2%}\n"
        f"Annualized Std. Dev: {benchmark_stats[1]:.2%}\n"
        f"Sharpe Ratio: {benchmark_stats[2]:.2f}"
    )
    ax1.text(0.02, 0.95, stats_text, transform=ax1.transAxes, fontsize=10,
             verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', facecolor='wheat', alpha=0.5))

    # --- Loop to create a plot for each stock in a 2-column grid ---
    for i, symbol in enumerate(stock_data.columns):
        row = 2 + (i // 2)
        col = i % 2
        ax = fig.add_subplot(gs[row, col])
        
        stock_price = stock_data[symbol]
        stock_ma = ma_data[symbol]
        stock_positions = positions[symbol]

        ax.plot(stock_price, label=f'{symbol} Price', color='black', alpha=0.7, linewidth=1.5)
        ax.plot(stock_ma, label=f'{MOVING_AVERAGE_WINDOW}-Day MA', color='red', linestyle='--', linewidth=1.5)
        
        buy_signals = stock_price[(stock_positions == 1) & (stock_positions.shift(1) == 0)]
        sell_signals = stock_price[(stock_positions == 0) & (stock_positions.shift(1) == 1)]

        ax.plot(buy_signals.index, buy_signals, '^', markersize=8, color='green', label='Buy')
        ax.plot(sell_signals.index, sell_signals, 'v', markersize=8, color='red', label='Sell')

        ax.set_title(f'{symbol} Price and Trading Signals', fontsize=12)
        ax.set_ylabel('Price (USD)', fontsize=10)
        ax.legend(loc='upper left', fontsize=9)
        ax.grid(True, linestyle='--', alpha=0.6)
        
        # Add x-axis label to the bottom-most plots
        if row == (stock_chart_rows + 1):
             ax.set_xlabel('Date', fontsize=10)


    # --- Save the chart ---
    plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # Adjust layout
    if not os.path.exists(CHART_OUTPUT_FOLDER):
        os.makedirs(CHART_OUTPUT_FOLDER)
    
    timestamp = dt.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = os.path.join(CHART_OUTPUT_FOLDER, f'performance_analysis_{timestamp}.png')
    
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"\nChart saved successfully to: {filename}")
    
    plt.show()

def main():
    """Main function to run the backtest."""
    stock_data = download_data(STOCK_SYMBOLS, start=START_DATE, end=END_DATE)
    benchmark_data = download_data(BENCHMARK_SYMBOL, start=START_DATE, end=END_DATE)
    risk_free_data = download_data(RISK_FREE_SYMBOL, start=START_DATE, end=END_DATE)
    
    daily_risk_free = risk_free_data / (100 * 360)

    strategy_returns, positions, ma_data = calculate_strategy_returns(stock_data, MOVING_AVERAGE_WINDOW)
    benchmark_returns = calculate_benchmark_returns(benchmark_data)

    aligned_returns = pd.concat([strategy_returns, benchmark_returns, daily_risk_free], axis=1).dropna()
    aligned_returns.columns = ['Strategy', 'Benchmark', 'RiskFree']
    
    cumulative_strategy = (1 + aligned_returns['Strategy']).cumprod()
    cumulative_benchmark = (1 + aligned_returns['Benchmark']).cumprod()

    strategy_stats = calculate_statistics(aligned_returns['Strategy'], aligned_returns['RiskFree'])
    benchmark_stats = calculate_statistics(aligned_returns['Benchmark'], aligned_returns['RiskFree'])

    print("\n--- Strategy Performance ---")
    print(f"Annualized Mean Return: {strategy_stats[0]:.2%}")
    print(f"Annualized Std. Deviation: {strategy_stats[1]:.2%}")
    print(f"Annualized Sharpe Ratio: {strategy_stats[2]:.2f}")

    print("\n--- S&P 500 Benchmark Performance ---")
    print(f"Annualized Mean Return: {benchmark_stats[0]:.2%}")
    print(f"Annualized Std. Deviation: {benchmark_stats[1]:.2%}")
    print(f"Annualized Sharpe Ratio: {benchmark_stats[2]:.2f}")

    plot_and_save_charts(cumulative_strategy, cumulative_benchmark, strategy_stats, benchmark_stats, stock_data, ma_data, positions, START_DATE, END_DATE)

if __name__ == "__main__":
    main()
