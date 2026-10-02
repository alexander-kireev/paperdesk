from decimal import Decimal


class Position:
    def __init__(self, stock, number_of_shares, user_id, total_value=None, position_id=None, last_price_per_share=None):   
        self.user_id = user_id
        self.company_name = stock.company_name
        self.symbol = stock.symbol
        self.price_per_share = Decimal(str(stock.price)).quantize(Decimal("0.01"))
        self.number_of_shares = number_of_shares
        self.total_value = (
            Decimal(str(total_value)).quantize(Decimal("0.01"))
            if total_value is not None
            else None
        )

        # optional
        if position_id:
            self.position_id = position_id

        # calculate total value of position if it was not provided as an arg
        if total_value is None:
            self.total_value = self.price_per_share * self.number_of_shares

        # ensure last_price is not left as null
        if last_price_per_share is None:
            self.last_price_per_share = stock.price
        else:
            self.last_price_per_share = Decimal(str(last_price_per_share)).quantize(Decimal("0.01"))




