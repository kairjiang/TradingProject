import config
import threading
import time
import pandas as pd
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order

class IBapi(EWrapper, EClient):
    def __init__(self, symbols):
        EClient.__init__(self, self)
        self.symbols = symbols
        self.data = {}
        self.signals = {}
        self.owned_stocks = {symbol: False for symbol in symbols}
        self.nextorderId = None
        self.data_received_event = threading.Event()

    def historicalData(self, reqId, bar):
        """Callback for receiving historical data."""
        if reqId not in self.data:
            self.data[reqId] = []
        self.data[reqId].append([bar.date, bar.close])

    def historicalDataEnd(self, reqId, start, end):
        """Callback for when historical data download is finished."""
        print(f"Historical data download finished for request {reqId}.")
        
        symbol = self.symbols[reqId - 1]
        df = pd.DataFrame(self.data[reqId], columns=['Date', 'Close'])
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        
        df['MA200'] = df['Close'].rolling(window=200).mean()
        
        if not df.empty and 'MA200' in df.columns and not df[['Close', 'MA200']].iloc[-1].isnull().any():
            last_price = df['Close'].iloc[-1]
            last_ma = df['MA200'].iloc[-1]
            self.signals[symbol] = 1 if last_price > last_ma else 0
            print(f"Signal for {symbol}: {'BUY' if self.signals[symbol] == 1 else 'SELL'}")
        else:
            self.signals[symbol] = 0
            print(f"Could not generate signal for {symbol} due to insufficient data.")
        
        if len(self.signals) == len(self.symbols):
            self.data_received_event.set()

    def nextValidId(self, orderId):
        super().nextValidId(orderId)
        self.nextorderId = orderId
        print(f"The next valid order id is: {self.nextorderId}")

    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        print(f"OrderStatus. Id: {orderId}, Status: {status}, Filled: {filled}, Remaining: {remaining}")

    def openOrder(self, orderId, contract, order, orderState):
        print(f"OpenOrder. PermId: {order.permId}, Symbol: {contract.symbol}, Action: {order.action}, Quantity: {order.totalQuantity}")

    def execDetails(self, reqId, contract, execution):
        print(f"ExecDetails. Symbol: {contract.symbol}, Shares: {execution.shares}, Price: {execution.price}")
    
    def error(self, reqId, errorCode, errorString, advancedOrderReject=""):
        if 2100 <= errorCode <= 2110 or errorCode == 2158:
            return
        print(f"Error. Id: {reqId}, Code: {errorCode}, Msg: {errorString}")

def create_stock_contract(symbol):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = 'STK'
    contract.exchange = 'SMART'
    contract.currency = 'USD'
    return contract

def create_market_order(action, quantity):
    """Creates a market order object without unsupported attributes."""
    order = Order()
    order.action = action.upper()
    order.totalQuantity = quantity
    order.orderType = 'MKT'
    order.eTradeOnly = False
    order.firmQuoteOnly = False
    return order

def main():
    app = IBapi(config.SYMBOLS)
    
    try:
        app.connect(config.HOST, config.PORT, clientId=config.CLIENT_ID)
        print("Connecting to TWS/Gateway...")
        
        api_thread = threading.Thread(target=app.run, daemon=True)
        api_thread.start()
        
        while app.nextorderId is None:
            print("Waiting for connection...")
            time.sleep(1)

        for i, symbol in enumerate(symbols):
            print(f"Requesting historical data for {symbol}...")
            app.reqHistoricalData(
                reqId=i + 1,
                contract=create_stock_contract(symbol),
                endDateTime='',
                durationStr='1 Y',
                barSizeSetting='1 day',
                whatToShow='ADJUSTED_LAST',
                useRTH=1,
                formatDate=1,
                keepUpToDate=False,
                chartOptions=[]
            )
            time.sleep(1)

        print("Waiting for historical data to be processed...")
        app.data_received_event.wait(timeout=60)

        if not app.data_received_event.is_set():
            print("Timed out waiting for historical data. Exiting.")
            return

        print("\nPlacing trades based on signals...")
        for symbol, signal in app.signals.items():
            is_owned = app.owned_stocks.get(symbol, False)
            
            if signal == 1 and not is_owned:
                print(f"Placing BUY order for {symbol}")
                order = create_market_order('BUY', 10)
                app.placeOrder(app.nextorderId, create_stock_contract(symbol), order)
                app.owned_stocks[symbol] = True
                app.nextorderId += 1
                time.sleep(1)
            
            elif signal == 0 and is_owned:
                print(f"Placing SELL order for {symbol}")
                order = create_market_order('SELL', 10)
                app.placeOrder(app.nextorderId, create_stock_contract(symbol), order)
                app.owned_stocks[symbol] = False
                app.nextorderId += 1
                time.sleep(1)
        
        print("\nFinished placing orders. Waiting for 10 seconds before disconnecting.")
        time.sleep(10)

    finally:
        print("Disconnecting...")
        app.disconnect()

if __name__ == "__main__":
    main()