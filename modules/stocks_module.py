"""
Stocks module — fetches market data for key tickers.
Uses yfinance (free, no API key needed).
Extend WATCHLIST to add your own tickers.
"""

import yfinance as yf
from datetime import datetime


# ── Customize your watchlist ────────────────────────────────────
WATCHLIST = [
    {"symbol": "SPY",  "label": "S&P 500"},
    {"symbol": "QQQ",  "label": "NASDAQ"},
    {"symbol": "BTC-USD", "label": "Bitcoin"},
    {"symbol": "^TNX", "label": "10Y Yield"},
    {"symbol": "^VIX", "label": "VIX"},
    {"symbol": "GLD",  "label": "Gold"},
]


def fetch():
    tickers = [t["symbol"] for t in WATCHLIST]
    data = yf.download(tickers, period="2d", interval="1d", progress=False, auto_adjust=True)

    results = []
    for item in WATCHLIST:
        sym = item["symbol"]
        try:
            closes = data["Close"][sym].dropna()
            if len(closes) < 2:
                raise ValueError("not enough data")
            prev  = float(closes.iloc[-2])
            curr  = float(closes.iloc[-1])
            chg   = curr - prev
            pct   = (chg / prev) * 100

            # Format value
            if sym == "BTC-USD":
                val_str = f"${curr:,.0f}"
            elif sym == "^TNX":
                val_str = f"{curr:.2f}%"
            elif sym == "^VIX":
                val_str = f"{curr:.1f}"
            else:
                val_str = f"${curr:,.2f}"

            chg_str = f"{'+'if chg>=0 else ''}{pct:.2f}%"
            direction = "up" if chg >= 0 else "down"

            results.append({
                "symbol":    sym,
                "label":     item["label"],
                "value":     val_str,
                "change":    chg_str,
                "direction": direction,
                "pct":       round(pct, 2),
            })
        except Exception as e:
            results.append({
                "symbol": sym, "label": item["label"],
                "value": "—", "change": "—", "direction": "flat", "pct": 0,
            })

    market_open = _is_market_open()
    return {"tickers": results, "market_open": market_open, "as_of": datetime.now().strftime("%I:%M %p ET")}


def _is_market_open():
    from datetime import datetime, timezone, timedelta
    et = datetime.now(timezone(timedelta(hours=-4)))  # rough ET
    if et.weekday() >= 5: return False
    return 9 <= et.hour < 16
