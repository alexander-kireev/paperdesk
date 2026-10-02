from datetime import date
from decimal import Decimal

from app.portfolio.portfolio_model import Portfolio
from app.position.position_model import Position
from app.stock.stock_model import Stock
from app.trade.trade_model import Trade
from app.transaction.transaction_model import Transaction
from app.user.user_model import User


def test_stock_price_is_decimal():
    stock = Stock("Example Company", "EXM", 12.346)

    assert stock.price == Decimal("12.35")
    assert isinstance(stock.price, Decimal)


def test_position_calculates_decimal_total():
    position = Position(Stock("Example Company", "EXM", "12.50"), 4, 1)

    assert position.total_value == Decimal("50.00")
    assert isinstance(position.last_price_per_share, Decimal)


def test_trade_calculates_decimal_total():
    trade = Trade(1, Stock("Example Company", "EXM", "12.50"), 4, "BUY")

    assert trade.trade_total == Decimal("50.00")


def test_transaction_amount_is_decimal():
    transaction = Transaction(1, "25.5", "DEPOSIT")

    assert transaction.amount == Decimal("25.50")


def test_portfolio_value_combines_cash_and_positions():
    user = User("alex", "smith", date(2000, 1, 1), "alex@example.com",
                cash_balance=Decimal("100.00"), id=1)
    positions = {"exm": object()}
    portfolio = Portfolio(user, Decimal("50.00"), positions)

    assert portfolio.positions_value == Decimal("50.00")
    assert portfolio.portfolio_value == Decimal("150.00")


def test_cash_only_portfolio_has_zero_position_value():
    user = User("alex", "smith", date(2000, 1, 1), "alex@example.com",
                cash_balance=Decimal("100.00"), id=1)
    portfolio = Portfolio(user)

    assert portfolio.positions_value == Decimal("0.00")
    assert portfolio.portfolio_value == Decimal("100.00")
