from app.user.user_model import User

def insert_user(cur, user):
    """ Accepts cursor and user object, inserts it into users table. """

    cur.execute("""
        INSERT INTO users (first_name, last_name, dob, email, password_hash, cash_balance)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        user.first_name, 
        user.last_name, 
        user.dob, 
        user.email, 
        user.password_hash,
        user.cash_balance
    ))

    return cur.rowcount > 0


def get_user_by_email(cur, email):
    """ Accepts cursor and email address, queries users table to find user based on
        email address, returns user object. """
    cur.execute("""
        SELECT id, first_name, last_name, dob, email, password_hash, cash_balance
        FROM users
        WHERE email=%s
    """, (email.strip().lower(),))
    
    row = cur.fetchone()
    
    if row:
        id, first_name, last_name, dob, email, password_hash, cash_balance = row
        return User(id=id, 
                    first_name=first_name, 
                    last_name=last_name,
                    dob=dob, 
                    password_hash=password_hash,
                    email=email,
                    cash_balance=cash_balance)
    else:
        return None
    

def get_user_by_id(cur, id):
    """ Accepts cursor and user id, queries users table to find user based on
    id, returns user object. """

    cur.execute("""
        SELECT id, first_name, last_name, dob, email, password_hash, cash_balance
        FROM users
        WHERE id=%s
    """, (id,))
    
    row = cur.fetchone()

    if row:
        id, first_name, last_name, dob, email, password_hash, cash_balance = row
        return User(id=id, 
                    first_name=first_name, 
                    last_name=last_name,
                    dob=dob, 
                    password_hash=password_hash,
                    email=email,
                    cash_balance=cash_balance)
    else:
        return None


def remove_user(cur, user_id):
    """ Accepts cursor and user_id, removes user from users table based on user_id. """

    cur.execute(""" DELETE FROM users WHERE id=%s """, (user_id,))
    return cur.rowcount > 0


def insert_user_email(cur, user_id, new_email):
    """  Accepts cursor, user_id and new_email, updates user's email in users table. """

    cur.execute(""" UPDATE users SET email=%s WHERE id=%s """,
                (new_email.strip().lower(), user_id))
    return cur.rowcount > 0


def insert_user_password(cur, user_id, new_password):
    """  Accepts cursor, user_id and new_password, updates user's password in users table. """

    cur.execute(""" UPDATE users SET password_hash=%s WHERE id=%s """, (new_password, user_id))
    return cur.rowcount > 0


def update_user_cash_balance(cur, user_id, new_balance):
    """  Accepts cursor, user_id and new_balance, updates user's cash balance in users table. """

    cur.execute(""" UPDATE users SET cash_balance=%s WHERE id=%s """, (new_balance, user_id))
    return cur.rowcount > 0


def insert_user_first_name(cur, user_id, first_name):
    """ Accepts a cursor, user_id and first_name, updates user's first name in table users. """

    cur.execute(""" UPDATE users SET first_name=%s WHERE id=%s """,
                (first_name, user_id))
    return cur.rowcount == 1


def insert_user_last_name(cur, user_id, last_name):
    """ Accepts a cursor, user_id and last_name, updates user's last name in table users. """

    cur.execute(""" UPDATE users SET last_name=%s WHERE id=%s """,
                (last_name, user_id))
    return cur.rowcount == 1


def insert_user_dob(cur, user_id, dob):
    """ Accepts a cursor, user_id and date of birth, then updates the user record. """

    cur.execute(""" UPDATE users SET dob=%s WHERE id=%s """,
                (dob, user_id))
    return cur.rowcount == 1


