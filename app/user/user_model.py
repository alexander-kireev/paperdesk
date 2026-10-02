class User:
    def __init__(self, first_name, last_name, dob, email, password_hash=None, 
                 cash_balance=None, id=None):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.dob = dob
        self.email = email
        self.password_hash = password_hash
        self.cash_balance = cash_balance
    
