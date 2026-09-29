"""Educational market simulator.

This project intentionally does not require a broker account, PAN/KYC, or market-data token.
Prices are simulated for paper-trading demonstrations and are not live NSE quotes.
"""
import hashlib
import math
import time
from dsa.algorithms import HashTable

STOCKS = [
    ("RELIANCE", "RELIANCE INDUSTRIES LTD", 2940.35, "Energy"),
    ("TCS", "TATA CONSULTANCY SERVICES LTD", 3987.45, "IT"),
    ("INFY", "INFOSYS LTD", 1560.80, "IT"),
    ("HDFCBANK", "HDFC BANK LTD", 1678.20, "Financial"),
    ("ICICIBANK", "ICICI BANK LTD", 1395.50, "Financial"),
    ("SBIN", "STATE BANK OF INDIA", 825.40, "Financial"),
    ("ITC", "ITC LTD", 430.25, "FMCG"),
    ("BHARTIARTL", "BHARTI AIRTEL LTD", 1925.10, "Telecom"),
    ("LT", "LARSEN & TOUBRO LTD", 3850.00, "Infrastructure"),
    ("SUNPHARMA", "SUN PHARMACEUTICAL INDUSTRIES LTD", 1745.60, "Healthcare"),
    ("MARUTI", "MARUTI SUZUKI INDIA LTD", 14520.00, "Automobile"),
    ("TATAMOTORS", "TATA MOTORS LTD", 710.40, "Automobile"),
    ("HINDUNILVR", "HINDUSTAN UNILEVER LTD", 2640.00, "FMCG"),
    ("ASIANPAINT", "ASIAN PAINTS LTD", 2385.00, "Consumer"),
    ("AXISBANK", "AXIS BANK LTD", 1215.00, "Financial"),
    ("KOTAKBANK", "KOTAK MAHINDRA BANK LTD", 2030.00, "Financial"),
    ("WIPRO", "WIPRO LTD", 505.00, "IT"),
    ("HCLTECH", "HCL TECHNOLOGIES LTD", 1540.00, "IT"),
    ("NTPC", "NTPC LTD", 390.00, "Energy"),
    ("POWERGRID", "POWER GRID CORPORATION OF INDIA LTD", 340.00, "Energy"),
]

CATALOG = []
for symbol, name, price, sector in STOCKS:
    CATALOG.append({"symbol": symbol, "name": name, "instrument_key": f"PAPER|{symbol}", "exchange": "NSE", "base_price": price, "sector": sector})

BY_KEY = HashTable()
BY_SYMBOL = HashTable()
for _stock in CATALOG:
    BY_KEY.insert(_stock["instrument_key"], _stock)
    BY_SYMBOL.insert(_stock["symbol"], _stock)


def configured():
    return False


def market_status():
    return {"mode": "PAPER MARKET", "source": "InvestTrack Educational Simulator", "live": False}


def _price_for(item):
    # Deterministic movement by minute so every refresh looks like a market tick,
    # while remaining reproducible and requiring no external service.
    minute = int(time.time() // 60)
    digest = hashlib.sha256(f"{item['symbol']}:{minute}".encode()).hexdigest()
    n = int(digest[:8], 16) / 0xFFFFFFFF
    wave = math.sin(minute / 11 + len(item["symbol"])) * 0.003
    move = (n - 0.5) * 0.012 + wave
    return round(max(0.01, item["base_price"] * (1 + move)), 2)


def search_stocks(query):
    q = (query or "").strip().lower()
    if len(q) < 1:
        return []
    return [
        {k: item[k] for k in ("symbol", "name", "instrument_key", "exchange", "sector")}
        for item in CATALOG if q in item["symbol"].lower() or q in item["name"].lower()
    ][:10]


def get_quotes(keys):
    out = {}
    for key in dict.fromkeys(keys or []):
        item = BY_KEY.get(key)
        if not item:
            continue
        last = _price_for(item)
        prev = item["base_price"]
        out[key] = {"last_price": last, "previous_close": prev, "change": round(last - prev, 2), "change_percent": round((last - prev) / prev * 100, 2)}
    return out


def get_prices(keys):
    return {k: v["last_price"] for k, v in get_quotes(keys).items()}
