from decimal import Decimal


class Trade:
    def __init__(self, user_id, stock, number_of_shares, trade_type,
                 trade_total=None, trade_id=None, timestamp=None):
        self.user_id = user_id
        self.company_name = stock.company_name
        self.symbol = stock.symbol
        self.price_per_share = stock.price
        self.number_of_shares = number_of_shares
        self.trade_type = trade_type

        # check if optional values were provided
        if trade_id:
            self.trade_id = trade_id
        if timestamp:
            self.timestamp = timestamp

        # if trade total was not provided as an arg, calculate it
        if trade_total is not None:
            self.trade_total = Decimal(str(trade_total)).quantize(Decimal("0.01"))
        else:
            self.trade_total = self.number_of_shares * self.price_per_share


