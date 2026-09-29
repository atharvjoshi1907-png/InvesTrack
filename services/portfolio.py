from collections import defaultdict
from datetime import date
from database.database import get_db
from services.market_data import get_quotes
from dsa.algorithms import LinkedList, Stack, merge_sort, max_heap_top, recursive_sum


def _positions(user_id):
    db = get_db()
    rows = db.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY id ASC", (user_id,)).fetchall()
    db.close()
    positions = {}
    realized_total = 0.0
    for row in rows:
        key = row["instrument_key"] or f"DEMO|{row['symbol']}"
        pos = positions.setdefault(key, {"symbol":row["symbol"],"company_name":row["company_name"] or row["symbol"],"instrument_key":key,"sector":row["sector"] or "Other","quantity":0.0,"cost":0.0,"realized_pnl":0.0})
        qty = float(row["quantity"]); price = float(row["price"]); typ = row["transaction_type"].upper()
        if typ == "BUY":
            pos["quantity"] += qty
            pos["cost"] += qty * price
        elif typ == "SELL":
            avg = pos["cost"] / pos["quantity"] if pos["quantity"] else 0.0
            realized = float(row["realized_pnl"] or (price - avg) * qty)
            pos["quantity"] -= qty
            pos["cost"] -= avg * qty
            pos["realized_pnl"] += realized
            realized_total += realized
    return {k:v for k,v in positions.items() if v["quantity"] > 1e-9}, realized_total


def get_portfolio_summary(user_id):
    positions, realized = _positions(user_id)
    db = get_db()
    acct = db.execute("SELECT * FROM accounts WHERE user_id=?", (user_id,)).fetchone()
    db.close()
    cash = float(acct["cash_balance"] if acct else 1000000.0)
    starting_cash = float(acct["starting_cash"] if acct else 1000000.0)
    quotes = get_quotes(list(positions.keys()))
    holdings=[]; invested_total=current_total=0.0
    for key,pos in positions.items():
        qty=pos["quantity"]; avg=pos["cost"]/qty if qty else 0
        quote=quotes.get(key,{"last_price":avg,"previous_close":avg,"change":0})
        current=float(quote["last_price"] or avg)
        invested=pos["cost"]; value=qty*current; profit=value-invested
        invested_total += invested; current_total += value
        holdings.append({"symbol":pos["symbol"],"company_name":pos["company_name"],"instrument_key":key,"sector":pos["sector"],"quantity":qty,"buy_price":avg,"current_price":current,"invested":invested,"current_value":value,"profit":profit,"return_percent":profit/invested*100 if invested else 0,"day_change":quote.get("change",0),"day_change_percent":quote.get("change",0)/quote.get("previous_close",current)*100 if quote.get("previous_close") else 0})
    holdings = merge_sort(holdings, key=lambda x: -x["current_value"])
    # DSA: stack keeps the most recently calculated holding available for inspection.
    recent_stack = Stack()
    for holding in holdings:
        recent_stack.push(holding["symbol"])
    equity = cash + current_total
    profit = equity - starting_cash
    return {"starting_cash":starting_cash,"cash_balance":cash,"total_invested":invested_total,"current_value":current_total,"equity":equity,"profit":profit,"return_percent":profit/starting_cash*100 if starting_cash else 0,"realized_pnl":realized,"holdings_count":len(holdings),"holdings":holdings,"dsa_top_holdings":max_heap_top(holdings,key=lambda x:x["profit"],limit=3),"dsa_recursive_value_check":recursive_sum([h["current_value"] for h in holdings])}


def transaction_linked_list(user_id):
    db=get_db()
    rows=db.execute("SELECT id, symbol, transaction_type, quantity, price, transaction_date FROM transactions WHERE user_id=? ORDER BY id ASC", (user_id,)).fetchall()
    db.close()
    ll=LinkedList()
    for row in rows:
        ll.append(dict(row))
    return ll


def record_snapshot(user_id):
    s=get_portfolio_summary(user_id); db=get_db()
    db.execute("INSERT OR REPLACE INTO portfolio_history(user_id,snapshot_date,invested,value) VALUES(?,?,?,?)",(user_id,date.today().isoformat(),s["total_invested"],s["current_value"]))
    db.commit(); db.close(); return s


def get_history(user_id):
    db=get_db(); rows=db.execute("SELECT snapshot_date, invested, value FROM portfolio_history WHERE user_id=? ORDER BY snapshot_date",(user_id,)).fetchall(); db.close()
    return [dict(r) for r in rows]


def get_sector_allocation(summary):
    sectors=defaultdict(float)
    for h in summary["holdings"]: sectors[h["sector"]]+=h["current_value"]
    return [{"sector":k,"value":v} for k,v in sorted(sectors.items(),key=lambda x:x[1],reverse=True)]
