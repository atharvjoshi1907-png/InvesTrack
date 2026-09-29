import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).parent / "portfolio.db"
STARTING_CASH = 1_000_000.0


def get_db():
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def _columns(db, table):
    return {row[1] for row in db.execute(f"PRAGMA table_info({table})").fetchall()}


def init_db():
    db = get_db()
    db.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    db.execute("""CREATE TABLE IF NOT EXISTS accounts (
        user_id INTEGER PRIMARY KEY, starting_cash REAL NOT NULL DEFAULT 1000000,
        cash_balance REAL NOT NULL DEFAULT 1000000, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)""")
    db.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, symbol TEXT NOT NULL,
        transaction_type TEXT NOT NULL, quantity REAL NOT NULL, price REAL NOT NULL,
        transaction_date TEXT NOT NULL, company_name TEXT DEFAULT '', instrument_key TEXT DEFAULT '',
        sector TEXT DEFAULT 'Other', realized_pnl REAL DEFAULT 0, status TEXT DEFAULT 'PAPER',
        order_id TEXT DEFAULT '')""")
    db.execute("""CREATE TABLE IF NOT EXISTS watchlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, symbol TEXT NOT NULL,
        company_name TEXT NOT NULL, instrument_key TEXT NOT NULL, UNIQUE(user_id, instrument_key))""")
    db.execute("""CREATE TABLE IF NOT EXISTS portfolio_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, snapshot_date TEXT NOT NULL,
        invested REAL NOT NULL, value REAL NOT NULL, UNIQUE(user_id, snapshot_date))""")
    db.commit()
    db.close()
