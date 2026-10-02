from decimal import Decimal


class Transaction:
    def __init__(self, user_id, amount, transaction_type, timestamp=None, transaction_id=None):
        self.user_id = user_id
        self.amount = Decimal(str(amount)).quantize(Decimal("0.01"))
        self.transaction_type = transaction_type
        self.timestamp = timestamp
        self.transaction_id = transaction_id
