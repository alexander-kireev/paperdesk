from decimal import Decimal

from yfinance import Ticker
from app.stock.stock_model import Stock


def create_stock(symbol):
    """ Accepts a stock symbol, fetches live stock data and returns stock object. """

    try:

        # format and retrieve data
        symbol = symbol.upper()
        data = Ticker(symbol).info
        price = data["regularMarketPrice"]

        company_name = data["shortName"]

        return Stock(company_name, symbol, price)

    except Exception:
        return None


def create_stocks(symbols):
    """ Accepts a list of stock symbols, returns a dictionary with stock symbols as keys and stock objects
        as values. """

    stocks = {}

    for symbol in symbols:
        stocks[symbol] = create_stock(symbol)

    return stocks


def live_stock_price(symbol):
    """ Accepts an equity symbol and returns its live price as a Decimal. """

    price = Ticker(symbol).fast_info["lastPrice"]
    return Decimal(str(price)).quantize(Decimal("0.01"))





