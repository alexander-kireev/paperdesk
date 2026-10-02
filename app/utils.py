import bcrypt
import re
from datetime import date
from decimal import Decimal, InvalidOperation

NAME_MIN_LEN = 1
NAME_MAX_LEN = 50

PASSWORD_MIN_LEN = 12
PASSWORD_MAX_LEN = 24

WITHDRAW_MIN_AMOUNT = Decimal("10.00")
WITHDRAW_MAX_AMOUNT = Decimal("1000000.00")



def email_is_valid(email):
    """ Return a normalised email address when valid, otherwise return a false value. """

    # ensure email is a string
    if not isinstance(email, str):
        return False

    email = email.strip().lower()

    # ensure string fits pattern of email type
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    match = re.match(pattern, email)
    if match is not None:
        return email
    else:
        return None


def hash_password(password):
    """ Accepts a password and returns a hash. """

    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password, hashed_password):
    """ Accepts a plaintext password and a hash, returns true if they match. """

    return bcrypt.checkpw(password.encode(), hashed_password.encode())


def validate_registration_data(data):
    """ Validate registration data and return a result dictionary. """

    first_name = valid_first_name(data["first_name"])

    if not first_name:
        return {
            "success": False,
            "message": "Invalid first name."
        }

    last_name = valid_last_name(data["last_name"])

    if not last_name:
        return {
            "success": False,
            "message": "Invalid last name."
        }

    dob = valid_dob(data["dob"])

    if not dob:
        return {
            "success": False,
            "message": "Invalid date of birth."
        }

    email = email_is_valid(data["email"])

    if not email:
        return {
            "success": False,
            "message": "Invalid email address."
        }

    password = valid_password(data["first_password"])

    if not password:
        return {
            "success": False,
            "message": """Password must contain at least one lowercase character, one uppercase character,
                        one number and be between 12 and 24 characters long."""
        }

    if not passwords_match(data["first_password"], data["second_password"]): #
        return {
            "success": False,
            "message": "Passwords must match."
        }

    return {
        "success": True,
        "data": {
            "first_name": first_name,
            "last_name": last_name,
            "dob": dob,
            "email": email,
            "password": password,
        },
    }


def valid_first_name(first_name):
    """ Return a normalised first name when it meets the validation rules. """

    try:
        first_name = first_name.lower()

        if not NAME_MIN_LEN <= len(first_name) <= NAME_MAX_LEN:
            return None

        if not first_name.isalpha():
            return None

        return first_name

    except (ValueError, TypeError):
        return None


def valid_last_name(last_name):
    """ Return a normalised last name when it meets the validation rules. """

    try:
        last_name = last_name.lower()

        if not NAME_MIN_LEN <= len(last_name) <= NAME_MAX_LEN:
            return None

        if not last_name.isalpha():
            return None

        return last_name

    except (ValueError, TypeError):
        return None


def valid_password(password):
    """ Accepts a password and checks if it is between 12 and 24 characters long
        and contains at least one digit, one uppercase and one lowercase character. """

    has_lowercase = False
    has_uppercase = False
    has_digit = False

    if not PASSWORD_MIN_LEN <= len(password) <= PASSWORD_MAX_LEN:
        return None

    for char in password:
        if char.isdigit():
            has_digit = True
        elif char.islower():
            has_lowercase = True
        elif char.isupper():
            has_uppercase = True
        else:
            return None

    if has_digit and has_lowercase and has_uppercase:
        return password
    else:
        return None


def passwords_match(password_1, password_2):
    """ Accepts two passwords, ensures they match. """

    return password_1 == password_2


def valid_deposit_and_withdraw_amount(amount):
    """ Accepts an amount and returns it as a Decimal if it is valid. """

    try:
        amount = Decimal(str(amount))
        if amount != amount.quantize(Decimal("0.01")):
            return None

        amount = amount.quantize(Decimal("0.01"))
        if not WITHDRAW_MIN_AMOUNT <= amount <= WITHDRAW_MAX_AMOUNT:
            return None
        return amount
    except (InvalidOperation, ValueError, TypeError):
        return None


def valid_num_shares(num_shares):

    try:
        num_shares = int(num_shares)

        if num_shares < 1 or num_shares > 100000:
            return None

        return num_shares

    except (ValueError, TypeError):
        return None


def valid_dob(value):
    if not isinstance(value, str):
        return None

    try:
        dob = date.fromisoformat(value.strip())
    except ValueError:
        return None

    if dob >= date.today():
        return None

    return dob


def valid_date_range(start_date, end_date):
    """ Return true when both dates form a valid chronological range, or both are empty. """

    if not start_date and not end_date:
        return True

    if not start_date or not end_date:
        return False

    try:
        start_date = date.fromisoformat(start_date)
        end_date = date.fromisoformat(end_date)
    except (TypeError, ValueError):
        return False

    return start_date <= end_date
