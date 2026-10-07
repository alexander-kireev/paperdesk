from decimal import Decimal

from yfinance import Ticker

from app.stock.stock_model import Stock


def create_stock(symbol):
    """Fetch current market data and return a stock object when available."""

    symbol = symbol.upper()

    try:
        ticker = Ticker(symbol)
        price = ticker.fast_info["lastPrice"]
    except Exception:
        return None

    try:
        company_name = ticker.info.get("shortName") or symbol
    except Exception:
        company_name = symbol

    return Stock(company_name, symbol, price)


def create_stocks(symbols):
    """Return stock objects keyed by symbol for the supplied symbol list."""

    stocks = {}

    for symbol in symbols:
        stocks[symbol] = create_stock(symbol)

    return stocks


def live_stock_price(symbol):
    """Return the latest available equity price as a Decimal."""

    price = Ticker(symbol).fast_info["lastPrice"]
    return Decimal(str(price)).quantize(Decimal("0.01"))
