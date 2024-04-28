import threading
import time
import yfinance as yf
import pandas as pd
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order

# Constants
STOCK_SYMBOL = "AAPL"
MOVING_AVERAGE_WINDOW = 200
QUANTITY = 10

class IBapi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.data = []
        self.historicalDataReceived = False

    def historicalData(self, reqId, bar):
        self.data.append([bar.date, bar.close])

    def historicalDataEnd(self, reqId, start, end):
        print("Historical data fetched")
        self.historicalDataReceived = True

    def nextValidId(self, orderId: int):
        self.nextorderId = orderId
        self.start_trading()

    def start_trading(self):
        print("Starting trading operations")
        self.fetch_historical_data()

    def fetch_historical_data(self):
        print("Fetching historical data")
        contract = self.stock_contract()
        self.reqHistoricalData(reqId=1, contract=contract, endDateTime='',
                               durationStr='2 Y', barSizeSetting='1 day',
                               whatToShow='ADJUSTED_LAST', useRTH=1, formatDate=1,
                               keepUpToDate=False, chartOptions=[])

    def stock_contract(self):
        contract = Contract()
        contract.symbol = STOCK_SYMBOL
        contract.secType = 'STK'
        contract.exchange = 'SMART'
        contract.currency = 'USD'
        return contract

    def check_strategy_and_trade(self):
        # Convert to DataFrame
        df = pd.DataFrame(self.data, columns=['Date', 'Close'])
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        # Calculate the moving average
        df['MA200'] = df['Close'].rolling(window=MOVING_AVERAGE_WINDOW).mean()
        # Determine the last price and MA
        last_price = df['Close'].iloc[-1]
        last_ma = df['MA200'].iloc[-1]
        # Decide and send order
        if last_price > last_ma:
            self.place_order("BUY")
        elif last_price < last_ma:
            self.place_order("SELL")

    def place_order(self, action):
        order = Order()
        order.action = action
        order.orderType = 'MKT'
        order.totalQuantity = QUANTITY
        order.orderId = self.nextorderId
        self.nextorderId += 1
        contract = self.stock_contract()
        self.placeOrder(order.orderId, contract, order)
        print(f"Placed {action} order for {QUANTITY} shares of {STOCK_SYMBOL}")

app = IBapi()
app.connect('127.0.0.1', 7497, 123)
api_thread = threading.Thread(target=app.run, daemon=True)
api_thread.start()

# Wait until historical data is fetched and trading decisions are made
while not app.historicalDataReceived:
    time.sleep(1)
app.disconnect()
