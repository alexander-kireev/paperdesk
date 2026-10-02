from datetime import datetime, timedelta
from decimal import Decimal
from app.db_core import DBCore

from app.trade.trade_model import Trade
from app.trade.trade_repo import (
    log_trade,
    get_trades
)

from app.position.position_model import Position
from app.position.position_repo import (
    get_user_positions_of_equity,
    log_position,
    close_position,
    update_position,
    update_positions_last_price
)
from app.user.user_repo import (
    get_user_by_id,
    update_user_cash_balance
)


def buy_stock(user_id, stock, number_of_shares):
    """ Record a share purchase and return a result dictionary. """
    
    try:
        with DBCore.get_connection() as conn:
            with conn.cursor() as cur:
                
                user = get_user_by_id(cur, user_id)
                trade_amount = stock.price * number_of_shares

                # ensure user has sufficient cash_balance to purchase shares
                if user.cash_balance < trade_amount:
                    return {
                        "success": False,
                        "message": "Insufficient cash balance to purchase shares."
                    }

                # instantiate trade object
                trade = Trade(user_id=user_id, stock=stock, number_of_shares=number_of_shares,
                            trade_type="BUY", trade_total=trade_amount)       
                
                # log trade in trades_log table
                if not log_trade(cur, trade):
                    return {
                        "success": False,
                        "message": "Failed to log trade."
                    }

                # instantiate position object
                position = Position(stock, number_of_shares, user_id)

                # log position in positions table
                if not log_position(cur, position):
                    return {
                        "success": False,
                        "message": "Failed to log position."
                    }

                new_cash_balance = user.cash_balance - trade_amount

                # update user's cash_balance
                if not update_user_cash_balance(cur, user_id, new_cash_balance):
                    return {
                        "success": False,
                        "message": "Failed to update user cash balance."
                    }           

                conn.commit()
                return {
                    "success": True,
                    "message": "Shares successfully purchased."
                }                 
                    
    except Exception:
        return {
            "success": False,
            "message": "Failed to purchase shares."
        }
            

def sell_stock(user_id, stock, number_of_shares):
    """ Sell shares from the user's open positions and return a result dictionary.
        This function does not allow short selling. """

    try:
        with DBCore.get_connection() as conn:
            with conn.cursor() as cur:
                
                # get positions object with list of positions of single stock
                positions = get_user_positions_of_equity(cur, user_id, stock.symbol)
                
                # ensure user has sufficient shares to sell desired amount
                if number_of_shares > positions.total_number_of_shares:
                    return {
                        "success": False,
                        "message": "Insufficient shares to sell."
                    }
                
                # set counters
                transaction_type = "SELL"
                total_value_shares_sold = Decimal("0.00")
                position_number = 0

                # run loop while shares remain to be sold
                while number_of_shares > 0:

                    # get earliest opened position object
                    first_position = positions.positions[position_number]

                    # check if entire position has more shares than user wants to sell
                    if number_of_shares > first_position.number_of_shares:
                        max_number_of_shares_for_trade = first_position.number_of_shares
                    else:
                        max_number_of_shares_for_trade = number_of_shares

                    # instantiate trade object
                    trade = Trade(user_id, stock, max_number_of_shares_for_trade, transaction_type)

                    # log trade in trades_log table
                    if not log_trade(cur, trade):
                        return {
                            "success": False,
                            "message": "Failed to log trade."
                        }
                    
                    # check if position must be closed as number of shares in position is now 0
                    if max_number_of_shares_for_trade == first_position.number_of_shares:
                        
                        # close position
                        if not close_position(cur, first_position):
                            return {
                                "success": False,
                                "message": "Failed to close position."
                            }
                    
                    # if position will have remaining shares and will need to be updated
                    else:
                        
                        # calculate new number_of_shares and total_value of position
                        updated_number_of_shares = first_position.number_of_shares - number_of_shares
                        updated_total_value = updated_number_of_shares * stock.price

                        # update the values in the object
                        first_position.number_of_shares = updated_number_of_shares
                        first_position.total_value = updated_total_value
                        first_position.last_price_per_share = stock.price

                        # update position in positions table
                        if not update_position(cur, first_position):
                            return {
                                "success": False,
                                "message": "Failed to update position."
                            }
                    
                    # update shares left to sell with number of shares sold in this iteration of loop
                    number_of_shares -= max_number_of_shares_for_trade

                    # update value of total shares sold to then update cash balance of user
                    total_value_shares_sold += trade.trade_total

                    # increment to move onto next position in list if need to sell more shares
                    position_number += 1

                user = get_user_by_id(cur, user_id)
                
                # update cash_balance in user object
                new_user_cash_balance = user.cash_balance + total_value_shares_sold

                # update cash_balance in users table
                if not update_user_cash_balance(cur, user_id, new_user_cash_balance):
                    return {
                        "success": False,
                        "message": "Failed to update user cash balance."
                    }

                # update any remaining positions with live price
                update_positions_last_price(cur, user_id, stock.symbol, stock.price)

                conn.commit()
                return {
                        "success": True,
                        "message": "Shares successfully sold."
                    }
        
    except Exception:
        return {
            "success": False,
            "message": "Failed to sell shares."
        }


def get_user_trade_history(user_id, start_date=None, end_date=None):
    """ Return a result dictionary containing the user's trades for an optional date range. """

    try:
        with DBCore.get_connection() as conn:
            with conn.cursor() as cur:

                # format end date to catch all trades until end of day
                if end_date:
                    end_date = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)

                # get list of trade objects from trades_log table
                trades_list = get_trades(cur, user_id, start_date, end_date)

                # ensure list exists
                if not trades_list:
                    return {
                        "success": False,
                        "message": "Failed to retrieve user trades from trades_log table."
                    }
                else:
                    return {
                        "success": True,
                        "message": trades_list
                    }
            
    except Exception:
        return {
            "success": False,
            "message": "Failed to retrieve user trades."
        }
      
