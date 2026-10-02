from app.transaction.transaction_model import Transaction

def get_transactions(cur, user_id, start_date, end_date):
    """ Accepts cursor and user_id and returns the user's transactions as
        trade objects. If user has not performed any trades, will return
        and empty list. If start and end date are provided, will filter 
        results to those dates. """

    # take path depending on whether start and end date were provided
    if start_date and end_date:
        cur.execute("""
            SELECT transaction_id, user_id, amount, transaction_type, created_at
            FROM transactions
            WHERE user_id=%s AND created_at >= %s AND created_at <= %s
            ORDER BY created_at DESC
        """, (user_id, start_date, end_date))
    else:
        cur.execute("""
            SELECT transaction_id, user_id, amount, transaction_type, created_at
            FROM transactions
            WHERE user_id=%s
            ORDER BY created_at DESC
        """, (user_id,))

    rows = cur.fetchall()
    transactions_list = []

    # if query returned any transaction rows
    if rows:
        for row in rows:

            # unpack each row, instantiate transaction object
            (transaction_id, user_id, amount, transaction_type, created_at) = row
            transaction = Transaction(user_id=user_id, amount=amount, transaction_type=transaction_type,
                                      timestamp=created_at, transaction_id=transaction_id)
            transactions_list.append(transaction)
    
    return transactions_list


def log_transaction(cur, transaction):
    """ Accepts cursor and transaction object, inserts it into transactions table. """

    cur.execute(""" 
            INSERT INTO transactions (user_id, amount, transaction_type)
            VALUES (%s, %s, %s)
            """, (
                transaction.user_id, transaction.amount, transaction.transaction_type
            ))

    return cur.rowcount > 0
