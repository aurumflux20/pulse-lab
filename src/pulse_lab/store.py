"""A small SQLite log of predictions: what the model said, what the market said, what happened."""
from __future__ import annotations

import sqlite3
from typing import Iterable, List, Optional, Tuple

SCHEMA = """CREATE TABLE IF NOT EXISTS predictions (
    pred_id TEXT PRIMARY KEY, ticker TEXT, asset TEXT,
    created_ts REAL, close_ts REAL,
    model_prob REAL, market_prob REAL,
    spot REAL, strike REAL, vol REAL, hours REAL,
    outcome INTEGER)"""

COLS = ("pred_id", "ticker", "asset", "created_ts", "close_ts", "model_prob", "market_prob",
        "spot", "strike", "vol", "hours", "outcome")


def connect(path: str) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.execute(SCHEMA)
    return con


def add(con: sqlite3.Connection, row: dict) -> bool:
    cur = con.execute(f"INSERT OR IGNORE INTO predictions ({','.join(COLS)}) "
                      f"VALUES ({','.join('?' * len(COLS))})", tuple(row.get(c) for c in COLS))
    con.commit()
    return cur.rowcount == 1


def unsettled_tickers(con: sqlite3.Connection, before_ts: float) -> List[str]:
    return [r[0] for r in con.execute(
        "SELECT DISTINCT ticker FROM predictions WHERE outcome IS NULL AND close_ts < ?", (before_ts,))]


def set_outcome(con: sqlite3.Connection, ticker: str, outcome: int) -> int:
    cur = con.execute("UPDATE predictions SET outcome=? WHERE ticker=? AND outcome IS NULL",
                      (int(outcome), ticker))
    con.commit()
    return cur.rowcount


def settled(con: sqlite3.Connection) -> List[Tuple[float, float, float, int]]:
    """(close_ts, model_prob, market_prob, outcome) for every settled prediction."""
    return [tuple(r) for r in con.execute(
        "SELECT close_ts, model_prob, market_prob, outcome FROM predictions "
        "WHERE outcome IS NOT NULL ORDER BY close_ts")]
