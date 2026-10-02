from app.db_core import DBCore
from app.portfolio.portfolio_model import Portfolio

from app.user.user_service import (
    get_user_by_id
)

from app.position.position_repo import get_user_equity_symbols
from app.position.position_service import (
    aggregate_all_equity_positions,
    aggregate_total_value_of_equity_positions,
    update_positions_in_table
)


def get_portfolio(user_id):
    """ Accepts a user_id and returns a result containing a portfolio object. """

    # update equity positions in positions table with live equity prices
    update_result = update_positions_in_table(user_id)
    if not update_result["success"]:
        return {
            "success": False,
            "message": "Failed to update portfolio prices."
        }

    try:
        with DBCore.get_connection() as conn:
            with conn.cursor() as cur:
                
                user = get_user_by_id(cur, user_id)

                if not user:
                    return {
                        "success": False,
                        "message": "Failed to fetch user."
                    }
                
                # check if user has any equities in positions table
                if equity_symbols := get_user_equity_symbols(cur, user_id):

                    # if they do, aggregate all positions into a single Position object
                    all_positions = aggregate_all_equity_positions(cur, user_id, equity_symbols)

                    # ensure positions are found
                    if not all_positions:
                        return {
                            "success": False,
                            "message": "Failed to aggregate positions."
                        }
                    
                    # get total value of all equities
                    total_equities_value = aggregate_total_value_of_equity_positions(all_positions)
                    
                    # ensure it is found
                    if not total_equities_value:
                        return {
                            "success": False,
                            "message": "Failed to tabulate total value of equities."
                        }

                    # instantiate portfolio object with equities and cash_balance
                    return {
                        "success": True,
                        "message": Portfolio(user, total_equities_value, all_positions)
                    }

                # if user has no open equity positions, instantiate portfolio object with cash_balance only
                else:
                    return {
                        "success": True,
                        "message": Portfolio(user)
                    }
                
    except Exception:
        return {
            "success": False,
            "message": "Failed to fetch portfolio."
        }







            




