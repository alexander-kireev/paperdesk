from app.db_core import DBCore
from decimal import Decimal

from app.position.position_model import Position
from app.position.position_repo import (
    get_user_equity_symbols,
    get_user_positions_of_equity,
    user_has_position_of_symbol,
    get_all_user_positions,
    update_list_of_positions
)

from app.stock.stock_model import Stock
from app.stock.stock_service import (
    live_stock_price
)


def get_user_position_by_symbol(user_id, symbol):
    """ Accepts a user_id and symbol, checks if user has open positions of that equity.
        Returns a result dictionary containing the combined Position when found. """
    
    try:
        with DBCore.get_connection() as conn:
            with conn.cursor() as cur:
                
                # check if user has any open positions of that equity
                if user_has_position_of_symbol(cur, user_id, symbol):
                    
                    # if so, aggregate all positions into one
                    result = aggregate_positions_of_single_equity(cur, user_id, symbol)
                    
                    if result:
                        return {
                            "success": True,
                            "message": result
                        }
                    else:
                        return {
                            "success": False,
                            "message": "Failed to get user's positions of equity."
                        }
                    
                return {
                    "success": False,
                    "message": f"User has no open positions of: {symbol}."
                }

    except Exception:
        return {
            "success": False,
            "message": "Failed to get user's positions of equity."
        }


def aggregate_positions_of_single_equity(cur, user_id, symbol):
    """ Accepts a cursor, user_id and symbol of equity. Queries positions
        table for ALL positions of this equity. Then, calculates the total
        number of shares held of this equity, the average price per share of
        this equity and the total value of all the shares. Returns one Position
        object containing the combined values. """

    # gets a list of objects of class Position
    # (all positions held by user of certain equity as a list of objects)
    positions = get_user_positions_of_equity(cur, user_id, symbol)

    # set counters
    total_shares = 0
    total_purchase_cost = Decimal("0.00")
    total_position_value = Decimal("0.00")

    # get the list containing the positions from the Positions object
    positions = positions.positions
    
    # calculate how many shares user owns and their total value
    for position in positions:
        total_shares += int(position.number_of_shares)
        total_purchase_cost += position.price_per_share * position.number_of_shares
        total_position_value += position.total_value

    # get average purchase price per share
    company_name = positions[0].company_name
    average_price_per_share = total_purchase_cost / total_shares
    last_price_per_share = positions[0].last_price_per_share
    
    # create stock and position objects, then return the combined position
    stock = Stock(company_name=company_name, symbol=symbol, price=average_price_per_share)
    return Position(stock=stock, number_of_shares=total_shares, user_id=user_id,
                    total_value=total_position_value,
                    last_price_per_share=last_price_per_share)


def aggregate_all_equity_positions(cur, user_id, equity_symbols):
    """ Accepts a cursor, user_id and list of symbols of equities owned by the user.
        It then calculates how many shares of each equity the user has, the average
        price per share and the total value of a holding. It returns a dictionary of
        Position objects, with each position accessed by its symbol. """

    # empty dictionary to store resulting dictionaries
    positions = {}

    # aggregate positions of an equity, for every symbol provided
    for symbol in equity_symbols:

        # store the resulting dictionary in a dictionary of dictionaries, accessed by symbol
        positions[symbol] = aggregate_positions_of_single_equity(cur, user_id, symbol)
        
    return positions


def aggregate_total_value_of_equity_positions(positions):
    """ Accepts dictionary of position objects, which can be accessed via
        their symbol, calculates the total value of positions, returns it
        as a Decimal. """

    total_equities_value = Decimal("0.00")
    for symbol in positions:
        total_equities_value += positions[symbol].total_value

    return total_equities_value


def update_positions_in_table(user_id):
    """ Accepts a user_id and updates every position held by user with a live price. """

    try:
        with DBCore.get_connection() as conn:
            with conn.cursor() as cur:
                
                # get list of symbols user has open positions of
                symbols = get_user_equity_symbols(cur, user_id)

                if not symbols:
                    return {
                        "success": True,
                        "message": "User has no positions to update."
                    }

                # fill a dict with symbol as key and live price as value
                symbols_with_live_prices = {}
                for symbol in symbols:
                    live_price = live_stock_price(symbol)
                    symbols_with_live_prices[symbol] = live_price

                # get list of every position user has as a position object
                positions = get_all_user_positions(cur, user_id)

                # iterate over list, updating last_price_per_share and total_value of position
                for position in positions:
                    symbol = position.symbol
                    live_price = symbols_with_live_prices[symbol]
                    new_total_value = position.number_of_shares * live_price
                    position.last_price_per_share = live_price
                    position.total_value = new_total_value
                
                # ensure each position was updated in the positions table
                if not update_list_of_positions(cur, positions):
                    return {
                        "success": False,
                        "message": "Failed to update list of positions in positions table."
                    }
                
                return {
                    "success": True,
                    "message": "Positions successfully updated in positions table."
                }

    except Exception:
        return {
            "success": False,
            "message": "Failed to update stock prices."
        }
