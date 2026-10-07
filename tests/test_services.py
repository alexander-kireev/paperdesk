from decimal import Decimal

from app.position.position_model import Position
from app.position.positions_model import Positions
from app.position import position_service
from app.stock.stock_model import Stock
from app.stock import stock_service


def test_create_stock_uses_fast_price_and_company_name(monkeypatch):
    class FakeTicker:
        def __init__(self, symbol):
            assert symbol == "AAPL"
            self.fast_info = {"lastPrice": 123.456}
            self.info = {"shortName": "Apple Inc."}

    monkeypatch.setattr(stock_service, "Ticker", FakeTicker)

    stock = stock_service.create_stock("aapl")

    assert stock.company_name == "apple inc."
    assert stock.symbol == "aapl"
    assert stock.price == Decimal("123.46")


def test_create_stock_keeps_price_when_company_info_fails(monkeypatch):
    class FakeTicker:
        def __init__(self, symbol):
            self.fast_info = {"lastPrice": 123.456}

        @property
        def info(self):
            raise ConnectionError("Company information unavailable")

    monkeypatch.setattr(stock_service, "Ticker", FakeTicker)

    stock = stock_service.create_stock("AAPL")

    assert stock.company_name == "aapl"
    assert stock.symbol == "aapl"
    assert stock.price == Decimal("123.46")


def test_live_stock_price_returns_decimal(monkeypatch):
    class FakeTicker:
        def __init__(self, symbol):
            assert symbol == "AAPL"
            self.fast_info = {"lastPrice": 123.456}

    monkeypatch.setattr(stock_service, "Ticker", FakeTicker)

    price = stock_service.live_stock_price("AAPL")

    assert price == Decimal("123.46")
    assert isinstance(price, Decimal)


def test_aggregate_positions_returns_combined_position(monkeypatch):
    first = Position(
        Stock("Example Company", "EXM", "10.00"),
        2,
        1,
        total_value="50.00",
        last_price_per_share="25.00",
    )
    second = Position(
        Stock("Example Company", "EXM", "20.00"),
        3,
        1,
        total_value="75.00",
        last_price_per_share="25.00",
    )
    positions = Positions(1, "exm", [first, second])

    monkeypatch.setattr(
        position_service,
        "get_user_positions_of_equity",
        lambda cursor, user_id, symbol: positions,
    )

    combined = position_service.aggregate_positions_of_single_equity(object(), 1, "exm")

    assert combined.number_of_shares == 5
    assert combined.total_value == Decimal("125.00")
    assert combined.price_per_share == Decimal("16.00")
    assert combined.last_price_per_share == Decimal("25.00")


def test_total_equity_value_is_decimal():
    positions = {
        "first": Position(Stock("First", "ONE", "10.00"), 2, 1),
        "second": Position(Stock("Second", "TWO", "7.50"), 4, 1),
    }

    total = position_service.aggregate_total_value_of_equity_positions(positions)

    assert total == Decimal("50.00")
    assert isinstance(total, Decimal)
