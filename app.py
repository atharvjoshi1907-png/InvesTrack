import os
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from database.database import init_db, get_db
from services.portfolio import get_portfolio_summary, record_snapshot, get_history, get_sector_allocation, _positions
from services.market_data import search_stocks, get_quotes, configured, market_status, CATALOG
from services.portfolio import transaction_linked_list
from dsa.algorithms import OrderQueue, PriceBST, SectorGraph, insertion_sort, selection_sort, merge_sort, binary_search, max_heap_top

load_dotenv()
app=Flask(__name__)
app.secret_key=os.getenv("FLASK_SECRET_KEY","dev-secret-change-me")
app.config["LIVE_TRADING_ENABLED"]=os.getenv("LIVE_TRADING_ENABLED","false").lower()=="true"
init_db()

def login_required(): return "user_id" in session

def current_user(): return session.get("user_id")

@app.route("/")
def home(): return render_template("index.html", api_configured=configured(), market_status=market_status())

@app.route("/register",methods=["GET","POST"])
def register():
    if request.method=="POST":
        name=request.form.get("name","").strip(); email=request.form.get("email","").strip().lower(); password=request.form.get("password","")
        if not name or not email or len(password)<6: flash("Enter your name, a valid email and a password of at least 6 characters."); return redirect(url_for("register"))
        db=get_db()
        if db.execute("SELECT id FROM users WHERE email=?",(email,)).fetchone(): db.close(); flash("An account with this email already exists."); return redirect(url_for("login"))
        db.execute("INSERT INTO users(name,email,password_hash) VALUES(?,?,?)",(name,email,generate_password_hash(password))); db.commit(); user=db.execute("SELECT id,name FROM users WHERE email=?",(email,)).fetchone(); db.execute("INSERT INTO accounts(user_id,starting_cash,cash_balance) VALUES(?,?,?)",(user["id"],1000000,1000000)); db.commit(); db.close()
        session["user_id"]=user["id"]; session["user_name"]=user["name"]; return redirect(url_for("dashboard"))
    return render_template("register.html")

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form.get("email","").strip().lower(); password=request.form.get("password",""); db=get_db(); user=db.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone(); db.close()
        if user and check_password_hash(user["password_hash"],password): session["user_id"]=user["id"]; session["user_name"]=user["name"]; return redirect(url_for("dashboard"))
        flash("Invalid email or password.")
    return render_template("login.html")

@app.route("/logout")
def logout(): session.clear(); return redirect(url_for("home"))

@app.context_processor
def globals_for_templates(): return {"live_trading":False,"api_configured":False,"market_status":market_status()}

@app.route("/dashboard")
def dashboard():
    if not login_required(): return redirect(url_for("login"))
    summary=record_snapshot(current_user())
    return render_template("dashboard.html",user_name=session.get("user_name","Investor"),summary=summary,history=get_history(current_user()),allocation=get_sector_allocation(summary))

@app.route("/portfolio")
def portfolio():
    if not login_required(): return redirect(url_for("login"))
    return render_template("portfolio.html",summary=get_portfolio_summary(current_user()))

@app.route("/trade",methods=["GET","POST"])
def trade():
    if not login_required(): return redirect(url_for("login"))
    if request.method=="POST":
        symbol=request.form.get("symbol","").strip().upper(); company=request.form.get("company_name","").strip(); key=request.form.get("instrument_key","").strip(); typ=request.form.get("transaction_type","BUY").upper(); sector=request.form.get("sector","Other"); trade_date=request.form.get("transaction_date") or date.today().isoformat()
        try: qty=float(request.form.get("quantity","")); price=float(request.form.get("price",""))
        except ValueError: flash("Quantity and price must be numbers."); return redirect(url_for("trade"))
        if typ not in ("BUY","SELL") or not symbol or not company or not key or qty<=0 or price<=0: flash("Select a stock and enter valid paper-trade details."); return redirect(url_for("trade"))
        positions,_=_positions(current_user()); pos=positions.get(key); db=get_db(); acct=db.execute("SELECT * FROM accounts WHERE user_id=?",(current_user(),)).fetchone()
        if not acct:
            db.execute("INSERT INTO accounts(user_id,starting_cash,cash_balance) VALUES(?,?,?)",(current_user(),1000000,1000000)); db.commit(); acct=db.execute("SELECT * FROM accounts WHERE user_id=?",(current_user(),)).fetchone()
        trade_value=qty*price
        if typ=="BUY" and acct["cash_balance"] < trade_value-1e-9: db.close(); flash(f"Insufficient paper cash. Available: ₹{acct['cash_balance']:,.2f}"); return redirect(url_for("trade"))
        if typ=="SELL" and (not pos or pos["quantity"] < qty-1e-9): db.close(); flash("You cannot sell more shares than you currently hold."); return redirect(url_for("trade"))
        # DSA: every paper order passes through a FIFO queue before database processing.
        order_queue=OrderQueue()
        order_queue.enqueue({"symbol":symbol,"type":typ,"quantity":qty,"price":price})
        order=order_queue.dequeue()
        realized=0.0
        if typ=="SELL":
            avg=pos["cost"]/pos["quantity"] if pos["quantity"] else 0.0; realized=(price-avg)*qty
            new_cash=acct["cash_balance"]+trade_value
        else:
            new_cash=acct["cash_balance"]-trade_value
        db.execute("INSERT INTO transactions(user_id,symbol,transaction_type,quantity,price,transaction_date,company_name,instrument_key,sector,realized_pnl,status) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(current_user(),symbol,typ,qty,price,trade_date,company,key,sector,realized,"PAPER"))
        db.execute("UPDATE accounts SET cash_balance=? WHERE user_id=?",(new_cash,current_user())); db.commit(); db.close()
        flash(f"Paper {typ} recorded: {qty:g} {symbol} at ₹{price:,.2f}. Cash balance: ₹{new_cash:,.2f}"); return redirect(url_for("portfolio"))
    return render_template("trade.html",today=date.today().isoformat())

@app.route("/transactions")
def transactions():
    if not login_required(): return redirect(url_for("login"))
    db=get_db(); rows=db.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY transaction_date DESC,id DESC",(current_user(),)).fetchall(); db.close(); return render_template("transactions.html",transactions=rows)

@app.route("/watchlist")
def watchlist():
    if not login_required(): return redirect(url_for("login"))
    db=get_db(); rows=db.execute("SELECT * FROM watchlist WHERE user_id=? ORDER BY id DESC",(current_user(),)).fetchall(); db.close(); quotes=get_quotes([r["instrument_key"] for r in rows]); return render_template("watchlist.html",watchlist=rows,quotes=quotes)

@app.route("/watchlist/add",methods=["POST"])
def watchlist_add():
    if not login_required(): return redirect(url_for("login"))
    symbol=request.form.get("symbol","").strip().upper(); company=request.form.get("company_name","").strip(); key=request.form.get("instrument_key","").strip()
    if symbol and company and key:
        db=get_db(); db.execute("INSERT OR IGNORE INTO watchlist(user_id,symbol,company_name,instrument_key) VALUES(?,?,?,?)",(current_user(),symbol,company,key)); db.commit(); db.close(); flash(f"{symbol} added to watchlist.")
    return redirect(url_for("watchlist"))

@app.route("/watchlist/delete/<int:item_id>",methods=["POST"])
def watchlist_delete(item_id):
    if not login_required(): return redirect(url_for("login"))
    db=get_db(); db.execute("DELETE FROM watchlist WHERE id=? AND user_id=?",(item_id,current_user())); db.commit(); db.close(); return redirect(url_for("watchlist"))

@app.route("/analytics")
def analytics():
    if not login_required(): return redirect(url_for("login"))
    summary=get_portfolio_summary(current_user()); return render_template("analytics.html",summary=summary,history=get_history(current_user()),allocation=get_sector_allocation(summary))

@app.route("/dsa-lab")
def dsa_lab():
    if not login_required(): return redirect(url_for("login"))
    summary=get_portfolio_summary(current_user())
    holdings=summary["holdings"]
    by_profit=insertion_sort(holdings,key=lambda x:-x["profit"])
    by_value=selection_sort(holdings,key=lambda x:-x["current_value"])
    by_symbol=merge_sort(holdings,key=lambda x:x["symbol"])
    # BST indexes the portfolio by current price.
    bst=PriceBST()
    for h in holdings: bst.insert(h["current_price"], h["symbol"])
    price_index=bst.inorder()
    # Graph connects holdings from the same sector; BFS demonstrates traversal.
    graph=SectorGraph()
    for i,a in enumerate(holdings):
        for b in holdings[i+1:]:
            if a["sector"]==b["sector"]: graph.add_edge(a["symbol"],b["symbol"])
    graph_start=holdings[0]["symbol"] if holdings else None
    graph_bfs=graph.bfs(graph_start) if graph_start else []
    transactions=transaction_linked_list(current_user()).to_list()
    return render_template("dsa_lab.html",summary=summary, insertion=by_profit, selection=by_value, merge=by_symbol, price_index=price_index, graph_bfs=graph_bfs, transactions=transactions, binary_search_example=binary_search(by_symbol, by_symbol[0]["symbol"], key=lambda x:x["symbol"]) if by_symbol else -1, heap=max_heap_top(holdings,key=lambda x:x["profit"],limit=5))

@app.route("/api/search")
def api_search():
    if not login_required(): return jsonify({"error":"Login required"}),401
    return jsonify({"results":search_stocks(request.args.get("q",""))})

@app.route("/api/quotes")
def api_quotes():
    if not login_required(): return jsonify({"error":"Login required"}),401
    keys=[x for x in request.args.get("keys","").split(",") if x]; return jsonify(get_quotes(keys))

@app.route("/api/portfolio")
def api_portfolio():
    if not login_required(): return jsonify({"error":"Login required"}),401
    return jsonify(get_portfolio_summary(current_user()))

@app.route("/health")
def health(): return jsonify({"status":"ok","mode":"paper_trading","market_data":"simulated_educational_prices","real_orders":False})

if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.getenv("PORT",5001)),debug=os.getenv("FLASK_DEBUG","false").lower()=="true")
