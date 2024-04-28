import threading
import time
import pandas as pd
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order


class IBapi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.data = {}
        self.positions = {}

    def historicalData(self, reqId, bar):
        if reqId not in self.data:
            self.data[reqId] = []
        self.data[reqId].append([bar.date, bar.close])
        print(f'Time: {bar.date}, Close: {bar.close}')

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        print("Historical data download finished", reqId, start, end)
        # Calculate moving average and generate signals
        df = pd.DataFrame(self.data[reqId], columns=['Date', 'Close'])
        df['MA200'] = df['Close'].rolling(window=200).mean()
        df['Position'] = (df['Close'] > df['MA200']).astype(int)
        self.positions[reqId] = df['Position'].iloc[-1]
        print(df.tail())

    def nextValidId(self, orderId: int):
        self.nextorderId = orderId
        print('The next valid order id is:', self.nextorderId)

    def orderStatus(self, orderId, status, filled, remaining, avgFullPrice,
                    permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        print('Order Status - ID:', orderId, 'Status:', status, 'Filled:', filled)

    def openOrder(self, orderId, contract, order, orderState):
        print('Open Order - ID:', orderId, 'Symbol:', contract.symbol, 'Action:', order.action)

    def execDetails(self, reqId, contract, execution):
        print('Order Executed:', contract.symbol, 'Exec ID:', execution.execId, 'Order ID:', execution.orderId,
              'Shares:', execution.shares)


def run_loop():
    app.run()


def stock_order(symbol):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = 'STK'
    contract.exchange = 'SMART'  # Choose appropriate exchange
    contract.currency = 'USD'
    return contract


app = IBapi()
app.connect('127.0.0.1', 7497, 123)
api_thread = threading.Thread(target=run_loop, daemon=True)
api_thread.start()
time.sleep(1)  # Ensure connection is established

# Define stock symbol
symbol = 'AAPL'

# Request historical data to calculate moving average
app.reqHistoricalData(reqId=1,
                      contract=stock_order(symbol),
                      endDateTime='',
                      durationStr='1 Y',
                      barSizeSetting='1 day',
                      whatToShow='ADJUSTED_LAST',
                      useRTH=1,
                      formatDate=1,
                      keepUpToDate=False,
                      chartOptions=[])

time.sleep(10)

# Determine current position
current_position = app.positions.get(1, 0)  # Latest position for the symbol

# Create and transmit order based on the signal
order = Order()
order.action = 'BUY' if current_position == 1 else 'SELL'
order.totalQuantity = 10
order.orderType = 'MKT'
order.orderId = app.nextorderId
app.nextorderId += 1
order.eTradeOnly = False
order.firmQuoteOnly = False

app.placeOrder(order.orderId, stock_order(symbol), order)
time.sleep(3)

app.disconnect()
