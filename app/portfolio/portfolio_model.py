from decimal import Decimal


class Portfolio:
    def __init__(self, user, total_equities_value=None, positions=None):
        self.user = user
        self.cash_balance = user.cash_balance

        # if user has open equity positions
        if positions:
            self.positions = positions
            self.positions_value = total_equities_value
            self.portfolio_value = self.positions_value + self.cash_balance
        # if user has no open equity positions
        else:
            self.positions = None
            self.positions_value = Decimal("0.00")
            self.portfolio_value = self.cash_balance
        
