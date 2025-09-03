import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

def simulate_ulty_backtest():
    """
    Performs a backtest for the High Income Strategy ETF
    using real historical data from yfinance.

    The simulation tracks a $10,000 investment from the ETF's inception,
    comparing a portfolio where dividends are reinvested to one where they are not.
    
    This version correctly uses the actual (Close) price for capital gains and
    manually reinvests the dividend payments.
    """
    
    # --- 1. Fetch Real Historical Data ---
    ticker = 'JEPQ'
    try:
        # Fetch raw historical price data (unadjusted for dividends)
        # We explicitly set auto_adjust=False to get the raw close price
        price_data = yf.download(ticker, start='2025-01-01', progress=False, auto_adjust=False)
        
        # Drop the MultiIndex to prepare for merging with dividend data
        price_data.columns = price_data.columns.droplevel(1)
        
        # Fetch dividend history separately and reset index to match price_data
        dividends = yf.Ticker(ticker).dividends.to_frame()
        dividends.index = pd.to_datetime(dividends.index.date)
        
        # Merge the two dataframes on their index
        df = price_data.join(dividends, how='left')
        df.rename(columns={'Dividends': 'dividend'}, inplace=True)
        
        if df.empty:
            print(f"Error: No data found for ticker {ticker}.")
            return
            
    except Exception as e:
        print(f"An error occurred while fetching data from yfinance: {e}")
        return

    # --- 2. Prepare Data for Backtest ---
    df.dropna(subset=['Close'], inplace=True)
    df.fillna({'dividend': 0}, inplace=True)
    df['price'] = df['Close']
    
    # --- 3. Define Simulation Parameters ---
    initial_investment = 100
    if df['price'].empty:
        print("Error: Price data is empty.")
        return
        
    initial_share_price = df['price'].iloc[0]
    
    # --- 4. Run Backtest with Dividend Reinvestment ---
    shares_reinvest = initial_investment / initial_share_price
    
    total_value_reinvest = [initial_investment]
    total_shares_reinvest = [shares_reinvest]
    
    # Loop starts from the second data point
    for i in range(1, len(df)):
        current_price = df['price'].iloc[i]
        
        # Check for dividend payment on the current day (ex-dividend date)
        if df['dividend'].iloc[i] > 0:
            dividend_per_share = df['dividend'].iloc[i]
            dividend_earned = shares_reinvest * dividend_per_share
            
            # Reinvest the earned dividend by buying more shares
            # We use the current day's price to simulate the purchase
            new_shares = dividend_earned / current_price
            shares_reinvest += new_shares
        
        # Calculate total portfolio value at the end of the day
        current_value = shares_reinvest * current_price
        total_value_reinvest.append(current_value)
        total_shares_reinvest.append(shares_reinvest)

    # --- 5. Run Backtest without Dividend Reinvestment ---
    shares_no_reinvest = initial_investment / initial_share_price
    cash_no_reinvest = 0.0
    
    total_value_no_reinvest = [initial_investment]
    
    for i in range(1, len(df)):
        current_price = df['price'].iloc[i]
        
        if df['dividend'].iloc[i] > 0:
            dividend_per_share = df['dividend'].iloc[i]
            dividend_earned = shares_no_reinvest * dividend_per_share
            cash_no_reinvest += dividend_earned
        
        # Calculate total portfolio value at the end of the day
        current_value = (shares_no_reinvest * current_price) + cash_no_reinvest
        total_value_no_reinvest.append(current_value)

    # --- 6. Calculate and Plot the Results ---
    df['yield'] = (df['dividend'] / df['price']) * 52 * 100
    
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(12, 20))
    
    # Plot 1: Portfolio Value
    ax1.plot(df.index, total_value_reinvest, label='With Dividend Reinvestment', color='teal')
    ax1.plot(df.index, total_value_no_reinvest, label='Without Reinvestment', color='salmon')
    ax1.set_title('Backtest with Real Data: Portfolio Value (2024-Present)')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Portfolio Value ($)')
    ax1.legend()
    ax1.grid(True)
    
    # Plot 2: Share Count
    ax2.plot(df.index, total_shares_reinvest, label='Total Shares with Reinvestment', color='darkblue')
    ax2.set_title('Backtest with Real Data: Total Shares Over Time')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Number of Shares')
    ax2.legend()
    ax2.grid(True)
    
    # Plot 3: ULTY Price
    ax3.plot(df.index, df['price'], label='Price', color='grey')
    ax3.set_title('Historical Price (2024-Present)')
    ax3.set_xlabel('Date')
    ax3.set_ylabel('Price ($)')
    ax3.legend()
    ax3.grid(True)

    # Plot 4: Dividend Yield
    # Only plot on days where a dividend was paid
    dividend_days = df[df['dividend'] > 0]
    ax4.bar(dividend_days.index, dividend_days['yield'], width=5, label='Annualized Dividend Yield', color='darkgreen')
    ax4.set_title('Backtest with Real Data: Annualized Dividend Yield')
    ax4.set_xlabel('Date')
    ax4.set_ylabel('Yield (%)')
    ax4.legend()
    ax4.grid(True)
    
    plt.tight_layout()
    plt.show()

# Run the backtest
if __name__ == "__main__":
    simulate_ulty_backtest()
