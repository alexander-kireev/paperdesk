import os
from functools import wraps
from datetime import datetime
from dotenv import load_dotenv

from app.transaction.transaction_service import get_user_transaction_history
from app.position.position_service import get_user_position_by_symbol
from app.portfolio.portfolio_service import get_portfolio
from app.stock.stock_service import create_stock
from app.exchange_data.exchange_service import ALL_SYMBOLS

from flask import (
    abort,
    Flask,
    session,
    request,
    render_template,
    redirect,
    url_for,
    flash,
    send_file,
)
from flask_wtf.csrf import CSRFProtect

from app.trade.trade_service import (
    buy_stock,
    sell_stock,
    get_user_trade_history,
)

from app.user.user_service import (
    register_user,
    authenticate_user,
    get_user,
    update_user_email,
    update_user_password,
    delete_user,
    update_user_details,
    deposit_user_funds,
    withdraw_user_funds,
)

from app.utils import (
    validate_registration_data,
    email_is_valid,
    passwords_match,
    verify_password,
    hash_password,
    valid_first_name,
    valid_last_name,
    valid_password,
    valid_deposit_and_withdraw_amount,
    valid_num_shares,
    valid_dob,
    valid_date_range,
)

from app.pdf_generator import (
    generate_portfolio_statement,
    generate_transaction_statement,
    generate_trade_statement,
)

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
csrf = CSRFProtect(app)


@app.template_filter()
def currency(value):
    """ Format a number as currency with commas and 2 decimals. """

    try:
        return f"{float(value):,.2f}"
    except (ValueError, TypeError):
        return value


@app.template_filter()
def toupper(value):
    """ Convert string to uppercase. """

    if value:
        return str(value).upper()
    return value


@app.template_filter()
def titlecase(value):
    """ Convert string to Title Case. """

    if value:
        return str(value).title()
    return value


@app.template_filter()
def shorttime(value):
    """ Format a datetime to show date + hours:minutes (no seconds/millis).
        Example: 2025-10-01 14:30 """
    
    if isinstance(value, datetime):
        return value.strftime("%d %b %Y %H:%M")
    try:
        parsed = datetime.fromisoformat(str(value))
        return parsed.strftime("%d %b %Y %H:%M")
    except Exception:
        return value


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        """ Ensures user is logged in before providing access to route. """

        if "user_id" not in session:
            return redirect(url_for("log_in"))
        return f(*args, **kwargs)
    
    return decorated_function


@app.route("/")
def home():
    """ Index html route, based on whether user is logged in or not. """

    if session.get("user_id"):
        return redirect("/portfolio")

    return render_template("index.html")


@app.route("/log_in", methods=["GET", "POST"])
def log_in():

    # POST request
    if request.method == "POST":

        # get input
        email = request.form["email"]
        password = request.form["password"]

        # log user in
        result = authenticate_user(email, password)

        # log user in if authentication was successful
        if result["success"]:
            user = result["message"]
            session["user_id"] = user.id
            return redirect("/portfolio")
        
        # if authentication was unsuccessful, display message
        else:
            flash(result["message"], "danger")
            return redirect("/log_in")

    # GET  request
    else:   
        return render_template("log_in.html")


@app.route("/sign_up", methods=["GET", "POST"])
def signup():

    # POST method
    if request.method == "POST":

        # collect input into object
        raw_data = {
            "first_name": request.form.get("first_name", "").strip(),
            "last_name": request.form.get("last_name", "").strip(),
            "dob": request.form.get("dob", "").strip(),
            "email": request.form.get("email", "").strip(),
            "first_password": request.form.get("first_password", ""),
            "second_password": request.form.get("second_password", "")
        }
        
        # validate input
        result = validate_registration_data(raw_data)
        if not result["success"]:
            flash(result["message"], "danger")
            return redirect("/sign_up")

        # register user
        result = register_user(result["data"])

        # if registration was successful, log user in
        if result["success"]:
            user = result["message"]
            session["user_id"] = user.id
            return redirect("/portfolio")
        
        # if registration was unsuccessful, display message
        else:
            flash(result["message"], "danger")
            return redirect("/sign_up")

    # GET request   
    else:
        return render_template("sign_up.html")


@app.route("/log_out", methods=["POST"])
@login_required
def log_out():
    session.clear()
    return redirect("/")


@app.route("/my_details")
@login_required
def my_details():
    user = get_user(session["user_id"])
    return render_template("my_details.html", user=user)


@app.route("/change_email", methods=["GET", "POST"])
@login_required
def change_email():
    """ Loads the change_email.html, allows user to change email address. """

    # POST request
    if request.method == "POST":

        # get input
        new_email = request.form.get("new_email", "").strip()
        password = request.form.get("password", "")

        # get user object
        user_id = session["user_id"]
        user = get_user(user_id)

        # ensure new email provided is valid
        if not email_is_valid(new_email):
            flash("Invalid email address.", "danger")
            return redirect("/change_email")

        
        # ensure user entered correct password
        if not verify_password(password=password, hashed_password=user.password_hash):
            flash("Incorrect password.", "danger")
            return redirect("/change_email")

        # update user email in table
        result = update_user_email(user_id, new_email, password)

        # if email was changed successfully
        if result["success"]:
            flash("Email address changed successfully.", "success")

        # if error occurred
        else:
            error = result["message"]
            flash(error, "danger")

        return redirect("/change_email")
    
    # GET request
    else:

        # get user object
        user_id = session["user_id"]
        user = get_user(user_id)
        
        return render_template("change_email.html", current_email=user.email)


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():

    # POST request
    if request.method == "POST":

        # get input
        current_password = request.form.get("current_password", "")
        new_password_1 = request.form.get("new_password_1", "")
        new_password_2 = request.form.get("new_password_2", "")

        # ensure input was provided
        if not current_password or not new_password_1 or not new_password_2:
            flash("Please enter your current and new passwords.", "danger")
            return redirect("/change_password")

        # ensure password is valid
        if not valid_password(new_password_1):
            flash("Password must contain at least one lowercase character, one uppercase character, one number and be between 12 and 24 characters long.", "danger")
            return redirect("/change_password")

        # get user
        user_id = session["user_id"]
        user = get_user(user_id)

        # ensure current password is correct
        if not verify_password(current_password, user.password_hash):     
            flash("Incorrect current password.", "danger")
            return redirect("/change_password")
        
        # ensure new passwords match
        if not passwords_match(new_password_1, new_password_2):
            flash("New passwords do not match.", "danger")
            return redirect("/change_password")
           

        # hash new password
        hashed_password = hash_password(new_password_1)

        # update password in table
        result = update_user_password(user_id, hashed_password)

        # if password was updated successfully
        if result["success"]:
            flash("Password changed successfully", "success")
        
        # if error occurred
        else:
            flash("Something went wrong. Please try again.", "danger")
           
        return redirect("/change_password")
    
    # GET request
    else:
        return render_template("change_password.html")


@app.route("/change_user_details", methods=["GET", "POST"])
@login_required
def change_user_details():

    user = get_user(session["user_id"])

    if request.method == "POST":

        # get input
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        dob = request.form.get("dob", "").strip()

        # validate and format input
        first_name = valid_first_name(first_name)
        last_name = valid_last_name(last_name)
        dob = valid_dob(dob)

        # ensure all input provided exists and is valid, else flash error
        if not first_name:
            flash("Please enter a valid first name.")
            return redirect("/change_user_details")
        if not last_name:
            flash("Please enter a valid last name.")
            return redirect("/change_user_details")
        if not dob:
            flash("Please enter a valid date of birth.")
            return redirect("/change_user_details")

        # update user details in users table        
        result = update_user_details(user_id=session["user_id"], user=user, first_name=first_name,
                                     last_name=last_name, dob=dob)
        
        if not result["success"]:
            flash("Sorry, something went wrong. Please try again.")
        else:
            flash("Your personal details have been successfully updated.")

        return redirect("/change_user_details")

    else:

        return render_template("change_user_details.html", first_name=user.first_name, 
                               last_name=user.last_name, dob=user.dob)
   

@app.route("/delete_account", methods=["GET", "POST"])
@login_required
def delete_account():

    # POST request
    if request.method == "POST":

        # get input
        password = request.form.get("password", "")

        # ensure input is present
        if not password:
            flash("Enter your password.", "danger")
            return redirect("/delete_account")
        
        # get user object
        user_id = session["user_id"]
        user = get_user(user_id)

        # ensure password is correct
        if not verify_password(password, user.password_hash):
            flash("Incorrect password.", "danger")
            return redirect("/delete_account")
        
        # delete user from table
        result = delete_user(user_id)

        # if deletion was successful, log user out
        if result["success"]:
            session.clear()
            return redirect("/")
        
        # if error occurred
        else:
            flash("Something went wrong. Please try again.", "danger")
            return redirect("/delete_account")

    # GET request
    else:
        return render_template("delete_account.html")


@app.route("/market", methods=["GET"])
@login_required
def market():

    symbol = request.args.get("ticker", "").strip().lower()

    # if symbol was provided (not initial page load)
    if len(symbol) > 0:
        if symbol.upper() not in ALL_SYMBOLS:
            flash("Please enter a valid ticker.", "danger")
            return redirect("/market")

        stock = create_stock(symbol)
        if not stock:
            flash("Something went wrong. Please try again.", "danger")
            return redirect("/market")

        user_id = session["user_id"]
        result = get_user_position_by_symbol(user_id, symbol)

        if result["success"]:
            position = result["message"]
            shares_held = position.number_of_shares
            average_price_per_share = position.price_per_share
            total_position_value = position.total_value
        else:
            shares_held = 0
            average_price_per_share = 0.00
            total_position_value = 0.00

        return render_template("market.html", stock=stock, shares_held=shares_held,
                               average_price_per_share=average_price_per_share,
                               total_position_value=total_position_value)

    return render_template("market.html")


@app.route("/sample_market", methods=["GET"])
def sample_market():

    symbol = request.args.get("ticker", "").strip().lower()

    # if symbol was provided (not initial page load)
    if len(symbol) > 0:
        if symbol.upper() not in ALL_SYMBOLS:
            flash("Please enter a valid ticker.", "danger")
            return redirect("/sample_market")

        stock = create_stock(symbol)
        if not stock:
            flash("Something went wrong. Please try again.", "danger")
            return redirect("/sample_market")

        shares_held = 0
        average_price_per_share = 0.00
        total_position_value = 0.00

        return render_template("sample_market.html", stock=stock, shares_held=shares_held,
                               average_price_per_share=average_price_per_share,
                               total_position_value=total_position_value)

    return render_template("sample_market.html")


@app.route("/place_order", methods=["POST"])
@login_required
def place_order():

    action = request.form.get("action")
    symbol = request.form.get("display_stock_symbol", "").strip().lower()
    user_id = session["user_id"]
    num_shares = valid_num_shares(request.form.get("order_amount"))

    if num_shares is None:
        flash("Please enter a valid number of shares.", "danger")
        return redirect("/market")

    if symbol.upper() not in ALL_SYMBOLS:
        flash("Something went wrong. Please try again.", "danger")
        return redirect("/market")

    stock = create_stock(symbol)
    if not stock:
        flash("Something went wrong. Please try again.", "danger")
        return redirect("/market")

    if action == "BUY":
        result = buy_stock(user_id, stock, num_shares)
        if result["success"]:
            flash("Shares purchased successfully.", "success")
        else:
            flash("Failed to purchase shares.", "danger")

    elif action == "SELL":
        result = sell_stock(user_id, stock, num_shares)
        if result["success"]:
            flash("Shares sold successfully.", "success")
        else:
            flash("Failed to sell shares.", "danger")

    else:
        flash("Invalid action. Please try again.", "danger")

    return redirect("/market")
        

@app.route("/portfolio", methods=["GET"])
@login_required
def portfolio():

    user_id = session["user_id"]
    result = get_portfolio(user_id)
    if not result["success"]:
        abort(500)

    portfolio = result["message"]
    return render_template("portfolio.html", portfolio=portfolio)


@app.route("/trades", methods=["GET"])
@login_required
def trades():

    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    if not valid_date_range(start_date, end_date):
        flash("Please enter a valid date range.", "danger")
        return redirect("/trades")

    user_id = session["user_id"]
    result = get_user_trade_history(user_id, start_date, end_date)
    trades = result["message"] if result["success"] else []

    return render_template("trades.html", trades=trades)


@app.route("/account", methods=["GET"])
@login_required
def account():

    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    if not valid_date_range(start_date, end_date):
        flash("Please enter a valid date range.", "danger")
        return redirect("/account")

    user_id = session["user_id"]
    result = get_user_transaction_history(user_id, start_date, end_date)
    if result["success"]:
        transactions = result["message"]
    else:
        flash(result["message"], "danger")
        transactions = []

    portfolio_result = get_portfolio(user_id)
    if not portfolio_result["success"]:
        abort(500)

    portfolio = portfolio_result["message"]
    return render_template("account.html", transactions=transactions, portfolio=portfolio)


@app.route("/deposit_funds", methods=["POST"])
@login_required
def deposit_funds():

    deposit_amount = valid_deposit_and_withdraw_amount(
        request.form.get("amount", request.form.get("deposit_amount"))
    )
    user_id = session["user_id"]

    if deposit_amount is None:
        flash("Please enter a valid deposit amount.", "danger")
        return redirect("/account")

    result = deposit_user_funds(user_id, deposit_amount)
    if result["success"]:
        flash(result["message"], "success")
    else:
        flash(result["message"], "danger")

    return redirect("/account")


@app.route("/withdraw_funds", methods=["POST"])
@login_required
def withdraw_funds():

    withdraw_amount = valid_deposit_and_withdraw_amount(
        request.form.get("amount", request.form.get("withdraw_amount"))
    )
    user_id = session["user_id"]

    if withdraw_amount is None:
        flash("Please enter a valid withdrawal amount.", "danger")
        return redirect("/account")

    result = withdraw_user_funds(user_id, withdraw_amount)
    if result["success"]:
        flash(result["message"], "success")
    else:
        flash(result["message"], "danger")

    return redirect("/account")


@app.route("/portfolio_statement", methods=["GET"])
@login_required
def portfolio_statement():

    # get user object
    user_id = session["user_id"]

    report = generate_portfolio_statement(user_id)
    if not report:
        flash("Failed generating portfolio statement.", "danger")
        return redirect("/portfolio")

    pdf_buffer, filename = report

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf",
    )


@app.route("/trade_history", methods=["POST"])
@login_required
def trade_history():

    # get user object and input
    user_id = session.get("user_id")  
    history_type = request.form.get("history_type")
    start_date = None
    end_date = None

    # check date constraints on query
    if history_type == "all":
        trades_result = get_user_trade_history(user_id)
    else:
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        if not valid_date_range(start_date, end_date):
            flash("Please enter a valid date range.", "danger")
            return redirect("/trades")
        trades_result = get_user_trade_history(user_id, start_date, end_date)

    # ensure trades were fetched
    if not trades_result["success"]:
        flash("No trades found for the selected period.", "danger")
        return redirect("/trades")

    # extract list of trade objects
    trades = trades_result["message"]  

    report = generate_trade_statement(
        user_id,
        trades,
        start_date=start_date,
        end_date=end_date,
    )
    if not report:
        flash("Failed generating trade history.", "danger")
        return redirect("/trades")

    pdf_buffer, filename = report

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf",
    )


@app.route("/transaction_history", methods=["POST"])
@login_required
def transaction_history():

    # get user object, input
    user_id = session["user_id"]
    history_type = request.form.get("history_type")
    start_date = None
    end_date = None

    # check date constraints on query
    if history_type == "all":
        tx_result = get_user_transaction_history(user_id)
    else:
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        if not valid_date_range(start_date, end_date):
            flash("Please enter a valid date range.", "danger")
            return redirect("/account")
        tx_result = get_user_transaction_history(user_id, start_date, end_date)

    # ensure transactions were fetched
    if not tx_result["success"]:
        flash("No transactions found for the selected period.", "danger")
        return redirect("/account")

    # extract list of transaction objects
    transactions = tx_result["message"]

    report = generate_transaction_statement(
        user_id,
        transactions,
        start_date=start_date,
        end_date=end_date,
    )
    if not report:
        flash("Failed generating transaction history.", "danger")
        return redirect("/account")

    pdf_buffer, filename = report

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf",
    )





if __name__ == "__main__":
    app.run(debug=False)
