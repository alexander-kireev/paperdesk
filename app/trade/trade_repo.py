from app.trade.trade_model import Trade
from app.stock.stock_model import Stock

def log_trade(cur, trade):
    """ Accepts cursor and trade object, inserts trade into trades_log table. """

    cur.execute(
        """ INSERT INTO trades_log (
                user_id, 
                company_name, 
                symbol, 
                price_per_share,
                number_of_shares,
                trade_total,
                trade_type
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            trade.user_id,
            trade.company_name,
            trade.symbol,
            trade.price_per_share,
            trade.number_of_shares,
            trade.trade_total,
            trade.trade_type
        ))
    return cur.rowcount > 0

def get_trades(cur, user_id, start_date, end_date):
    """ Accepts cursor, user_id and returns list of user's trades as
        trade objects. If user has not performed any trades, will return
        and empty list. If start and end date are provided, will filter 
        results to those dates. """

    # take path depending on whether start and end date were provided
    if start_date and end_date:
        cur.execute("""
            SELECT trade_id, user_id, company_name, symbol, executed_at,
                   price_per_share, number_of_shares, trade_total, trade_type
            FROM trades_log
            WHERE user_id = %s AND executed_at >= %s AND executed_at <= %s
            ORDER BY executed_at DESC
        """, (user_id, start_date, end_date)
        )
    else:
        cur.execute("""
            SELECT trade_id, user_id, company_name, symbol, executed_at,
                   price_per_share, number_of_shares, trade_total, trade_type
            FROM trades_log
            WHERE user_id=%s
            ORDER BY executed_at DESC
        """, (user_id,))

    rows = cur.fetchall()
    trades_list = []

    # if trades were found
    if rows:
        for row in rows:

            # unpack each row
            (trade_id, user_id, company_name, symbol,
             executed_at, price_per_share, number_of_shares,
             trade_total, trade_type) = row
            
            # refactor each row into trade object
            stock = Stock(company_name=company_name, symbol=symbol, price=price_per_share)
            trade = Trade(user_id=user_id, stock=stock, number_of_shares=number_of_shares,
                          trade_type=trade_type, trade_total=trade_total, trade_id=trade_id,
                          timestamp=executed_at)

            trades_list.append(trade)
        
    return trades_list

