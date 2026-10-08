"""Read-only public market data from Kalshi. No account, no key, no orders.

This module only ever sends GET requests to public endpoints. There is no
code anywhere in pulse-lab that can place a bet or move money.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import List, Optional

KALSHI_PUBLIC = "https://api.elections.kalshi.com/trade-api/v2"
CRYPTO_SERIES = ("KXBTCD", "KXETHD")   # daily Bitcoin and Ethereum price markets


def _cents(m: dict, dollars_key: str, cents_key: str) -> int:
    v = m.get(dollars_key)
    if v not in (None, ""):
        try:
            return round(float(v) * 100)
        except (TypeError, ValueError):
            return 0
    try:
        return int(m.get(cents_key) or 0)
    except (TypeError, ValueError):
        return 0


def parse_market(m: dict, now: Optional[datetime] = None) -> Optional[dict]:
    """Turn a raw market into the fields the lab uses, or None if it is not a usable price market."""
    now = now or datetime.now(timezone.utc)
    ticker = m.get("ticker", "")
    sm = re.search(r"-T(\d+\.?\d*)", ticker)
    up = ticker.upper()
    asset = "BTC" if "BTC" in up else ("ETH" if "ETH" in up else None)
    if not sm or not asset:
        return None
    ya = _cents(m, "yes_ask_dollars", "yes_ask")
    yb = _cents(m, "yes_bid_dollars", "yes_bid")
    if not (1 <= ya <= 99):
        return None
    close = m.get("close_time") or m.get("expiration_time") or ""
    try:
        close_dt = datetime.fromisoformat(close.replace("Z", "+00:00"))
    except ValueError:
        return None
    hours = (close_dt - now).total_seconds() / 3600
    if hours <= 0:
        return None
    market_prob = (ya + yb) / 200 if 1 <= yb <= ya else ya / 100
    return {"ticker": ticker, "asset": asset, "strike": float(sm.group(1)),
            "yes_ask": ya, "yes_bid": yb, "market_prob": market_prob,
            "close_ts": close_dt.timestamp(), "hours": hours}


def fetch_open_markets(series: str, session=None, limit: int = 200) -> List[dict]:
    import requests
    s = session or requests
    r = s.get(f"{KALSHI_PUBLIC}/markets", params={"series_ticker": series, "status": "open",
                                                  "limit": limit}, timeout=15)
    r.raise_for_status()
    return r.json().get("markets", [])


def fetch_result(ticker: str, session=None) -> Optional[int]:
    """1 if the market settled YES, 0 if NO, None if not settled yet."""
    import requests
    s = session or requests
    r = s.get(f"{KALSHI_PUBLIC}/markets/{ticker}", timeout=10)
    if not r.ok:
        return None
    mk = r.json().get("market", {})
    if mk.get("result") in ("yes", "no") and mk.get("status") in ("finalized", "settled"):
        return 1 if mk["result"] == "yes" else 0
    return None
