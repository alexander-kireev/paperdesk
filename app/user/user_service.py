from app.db_core import DBCore
from decimal import Decimal

from app.user.user_model import User
from app.user.user_repo import (
    insert_user,
    get_user_by_email,
    get_user_by_id,
    remove_user,
    update_user_cash_balance,
    insert_user_email,
    insert_user_password,
    insert_user_first_name,
    insert_user_last_name,
    insert_user_dob,
)

from app.transaction.transaction_model import Transaction
from app.transaction.transaction_repo import (
    log_transaction
)

from app.utils import  (
    email_is_valid, 
    hash_password,
    verify_password,
)

DEFAULT_USER_BALANCE = Decimal("10000.00")


def register_user(data):
    """ Accepts dict containing validated user registration data,
        instantiates a user object and inserts it into the users table. """

    try:
        with DBCore.get_connection() as conn:
            with conn.cursor() as cur:
                
                # ensure proposed email is not already in use
                if get_user_by_email(cur, data["email"]):
                    return {
                        "success": False,
                        "message": "Email is already in use."
                    }

                data["cash_balance"] = DEFAULT_USER_BALANCE
                data["password_hash"] = hash_password(data["password"])
                data.pop("password")

                # instantiate user object
                new_user = User(**data)

                # ensure user was inserted into users table
                if not insert_user(cur, new_user):
                    return {
                        "success": False,
                        "message": "Failed to insert user."
                    }
                
                # get newly registered user for the unique user_id
                registered_user = get_user_by_email(cur, data["email"])

                # instantiate transaction object to log initial deposit in transactions table
                transaction_type = "DEPOSIT"
                transaction = Transaction(registered_user.id, DEFAULT_USER_BALANCE, transaction_type)

                # ensure initial deposit transaction was logged in transactions table
                if not log_transaction(cur, transaction):
                    return {
                        "success": False,
                        "message": "Failed to log default deposit transaction."
                    }                
                
                conn.commit()
                return {
                        "success": True,
                        "message": registered_user
                }
                
    except Exception:
        return {
                "success": False,
                "message": "Failed to register user."
        }
    

def delete_user(user_id):
    """ Accepts a user_id, authenticates user, deletes the user record from the users table. """

    try:
        with DBCore.get_connection() as conn:
            with conn.cursor() as cur:
                
                # ensure user was removed from users table
                if not remove_user(cur, user_id):
                    conn.rollback()
                    return {
                    "success": False,
                    "message": "Failed to remove user from table."
                    }
                
                conn.commit()
                return {
                    "success": True,
                    "message": "User deleted successfully."
                }
              
    except Exception:
        return {
                "success": False,
                "message": "Failed to delete user."
        }
        

def update_user_email(user_id, new_email, password):
    """ Accepts a user_id, new_email and password, authenticates user, updates user email. """

    try:
        with DBCore.get_connection() as conn:
            with conn.cursor() as cur:

                # get user object
                user = get_user_by_id(cur, user_id)

                # ensure proposed new email is not already taken
                if get_user_by_email(cur, new_email):
                     return {
                        "success": False,
                        "message": "Email is already in use."
                    }                   

                # ensure provided password is correct
                if not verify_password(password, user.password_hash):
                    return {
                        "success": False,
                        "message": "Incorrect password."
                    }
                
                # ensure email was updated in users table
                if not insert_user_email(cur, user_id, new_email):
                    return {
                        "success": False,
                        "message": "Failed to update email in database."
                    }

                conn.commit()
                return {
                    "success": True,
                    "message": "Email successfully updated."
                }
                
    except Exception:
        return {
                "success": False,
                "message": "Failed to update user email."
        }
    

def update_user_password(user_id, new_password_hash):
    """ Accepts a user_id and new_password_hash, updates user password. """

    try:
        with DBCore.get_connection() as conn:
            with conn.cursor() as cur:

                # ensure password was updated in users table
                if not insert_user_password(cur, user_id, new_password_hash):
                    return {
                        "success": False,
                        "message": "Failed to insert new password into database."
                    }
                
                conn.commit()
                return {
                    "success": True,
                    "message": "Password successfully updated."
                }
                
    except Exception:
        return {
                "success": False,
                "message": "Failed to update user password."
        }
    

def deposit_user_funds(user_id, amount):
    """ Accepts a user_id and amount to deposit, updates the users table with the new cash balance. """
    conn = DBCore.get_connection()

    try:
        with conn:
            with conn.cursor() as cur:

                # get user object
                user = get_user_by_id(cur, user_id)

                # calculate new user cash_balance
                new_balance = user.cash_balance + amount

                # ensure cash_balance was updated in users table
                if not update_user_cash_balance(cur, user_id, new_balance):
                    return {
                        "success": False,
                        "message": "Failed to update user cash balance in table."
                    }
                
                # instantiate transaction object to log it in transaction table
                transaction_type = "DEPOSIT"
                transaction = Transaction(user_id, amount, transaction_type)

                # ensure transaction was logged
                if not log_transaction(cur, transaction):
                    return {
                            "success": False,
                            "message": "Failed to log deposit in transactions table."
                    }                  

                conn.commit()
                return {
                    "success": True,
                    "message": "Funds successfully deposited."
                }

    except Exception:
        return {
                "success": False,
                "message": "Failed to deposit funds."
        }
    

def withdraw_user_funds(user_id, amount):
    """ Accepts a user_id and amount to withdraw, then updates the user's cash balance. """
    conn = DBCore.get_connection()

    try:
        with conn:
            with conn.cursor() as cur:
                
                user = get_user_by_id(cur, user_id)

                # calculate new user cash_balance
                new_balance = user.cash_balance - amount

                # ensure balance is positive, meaning user has sufficient funds to withdraw
                if new_balance < 0:
                    return {
                        "success": False,
                        "message": "Insufficient cash balance to withdraw requested sum."
                    }            

                # ensure cash_balance was updated in users table
                if not update_user_cash_balance(cur, user_id, new_balance):
                    return {
                        "success": False,
                        "message": "Failed to update user cash balance in database."
                    }

                # instantiate transaction object to log it in transaction table
                transaction_type = "WITHDRAW"
                transaction = Transaction(user_id, amount, transaction_type)

                # ensure transaction was logged
                if not log_transaction(cur, transaction):
                    return {
                            "success": False,
                            "message": "Failed to log withdrawal in transactions table."
                    }                            

                conn.commit()
                return {
                    "success": True,
                    "message": "Funds successfully withdrawn."
                }            

    except Exception:
        return {
                "success": False,
                "message": "Failed to withdraw funds."
        }   
 

def authenticate_user(email, password):
    """ Accepts email and password, returns True and user object if email is registered to
        a user and password matches. """

    try:
        with DBCore.get_connection() as conn:
            with conn.cursor() as cur:

                user = get_user_by_email(cur, email)

                # ensure user has been found
                if not user:
                    return {
                        "success": False,
                        "message": "Invalid email address or password."
                    }
                
                # ensure password is correct
                if not verify_password(password, user.password_hash):
                    return {
                        "success": False,
                        "message": "Invalid email address or password."
                    }

                return {
                    "success": True,
                    "message": user 
                }

    except Exception:
        return {
            "success": False,
            "message": "Failed to log in. Please try again."
        }


def get_user(data_point):
    """ Accepts an int user_id or an email address. If such a user exists, returns
        user object. """

    # check if email was provided and is registered to an account
    try:
        with DBCore.get_connection() as conn:
            with conn.cursor() as cur:

                if email_is_valid(data_point):
                    return get_user_by_email(cur, data_point)
                
                # check if user_id was provided and is valid
                else:
                    try:
                        user_id = int(data_point)
                        return get_user_by_id(cur, user_id)
                    except (ValueError, TypeError):
                        return None

    except Exception:
        return None
    

def update_user_details(user_id, user, first_name=None, last_name=None, dob=None):
    """ Accepts a user_id, user object and optional user details. Updates users table
        with new user personal details. """

    try:
        with DBCore.get_connection() as conn:
            with conn.cursor() as cur:
                
                if first_name:
                    if first_name != user.first_name:
                        if not insert_user_first_name(cur, user_id, first_name):
                            raise Exception

                if last_name:
                    if last_name != user.last_name:
                        if not insert_user_last_name(cur, user_id, last_name):
                            raise Exception

                if dob:
                    if dob != user.dob:
                        if not insert_user_dob(cur, user_id, dob):
                            raise Exception
       
                return { 
                    "success": True,
                    "message": "User personal details successfully updated"
                }

    except Exception:
        return {
            "success": False,
            "message": "Failed to update user details."
        }
