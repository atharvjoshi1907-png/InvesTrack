# InvestTrack — Paper Trading Portfolio Tracker

InvestTrack is a Python Flask college project that simulates stock-market investing without requiring a broker account, PAN/KYC, API token, or real-money orders.

## What it does
- User registration/login
- ₹10,00,000 virtual starting cash per account
- NSE-style stock search using a built-in educational stock catalogue
- Paper BUY/SELL transactions
- Cash balance and portfolio equity tracking
- Weighted-average cost calculation
- Realized and unrealized P&L
- Transaction history
- Watchlist
- Portfolio analytics and sector allocation
- Historical portfolio snapshots
- Responsive fintech UI

## Market-data note
The project intentionally uses simulated educational prices. Prices move in a deterministic minute-based simulation so the interface can demonstrate refreshing market values without claiming to provide live NSE data. It does not place real orders.

NSE's official market-data policy distinguishes real-time/licensed market data from educational/non-commercial uses. For this academic project, simulated paper-market data avoids requiring personal broker KYC or redistributing licensed real-time quotes.

## Run locally
```bash
python3 -m pip install -r requirements.txt
cp .env.example .env
python3 app.py
```
Open http://127.0.0.1:5000 (or the PORT shown by the app).

## Render
Build: `pip install -r requirements.txt`
Start: `gunicorn app:app`

SQLite is suitable for a classroom demo. For a persistent public deployment, migrate the database to PostgreSQL.

## DSA Version
InvestTrack is now also an explicit Data Structures & Algorithms project. The `dsa/` package implements and uses:
- Hash table with separate chaining for stock lookup.
- Singly linked list for transaction history.
- Stack for recent analysis state.
- FIFO queue for paper-order processing.
- Binary search tree for price indexing and inorder traversal.
- Graph + BFS for same-sector relationships.
- Insertion sort, selection sort and merge sort for portfolio ordering.
- Binary search for sorted symbol lookup.
- Max heap for top P&L holdings.
- Recursion for portfolio aggregation demonstration.

The `/dsa-lab` page exposes these implementations using the user's real paper-trading data so the structures are part of the application rather than decorative code.
