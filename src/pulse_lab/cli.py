"""pulse-lab command line.

  pulse-lab demo                 offline: simulate data and score it (no internet)
  pulse-lab scan                 log model vs market for open BTC/ETH markets (read-only)
  pulse-lab settle               fill in outcomes for markets that have closed
  pulse-lab eval                 Brier score: model vs market
  pulse-lab research             train/test check (needs the [research] extra)
"""
from __future__ import annotations

import argparse
import sys
import time

from . import __version__, evaluate, store


def _scan(con) -> int:
    from .markets import CRYPTO_SERIES, fetch_open_markets, parse_market
    from .model import fetch_spot_and_vol, prob_above
    spots, n = {}, 0
    now = time.time()
    for series in CRYPTO_SERIES:
        for raw in fetch_open_markets(series):
            m = parse_market(raw)
            if (not m or m["hours"] > 48 or not (0.05 <= m["market_prob"] <= 0.95)
                    or m["yes_bid"] < 1 or m["yes_ask"] - m["yes_bid"] > 10):
                continue
            if m["asset"] not in spots:
                spots[m["asset"]] = fetch_spot_and_vol(m["asset"])
            spot, vol = spots[m["asset"]]
            p = prob_above(spot, m["strike"], vol, m["hours"]) if spot and vol else None
            if p is None:
                continue
            row = {"pred_id": f"{m['ticker']}|{int(now // 7200)}", "ticker": m["ticker"], "asset": m["asset"],
                   "created_ts": now, "close_ts": m["close_ts"], "model_prob": round(p, 4),
                   "market_prob": round(m["market_prob"], 4), "spot": spot, "strike": m["strike"],
                   "vol": round(vol, 4), "hours": round(m["hours"], 3), "outcome": None}
            n += store.add(con, row)
    return n


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="pulse-lab", description="Forecast lab. Read-only. No trading.")
    ap.add_argument("--version", action="version", version=f"pulse-lab {__version__}")
    ap.add_argument("--db", default="pulse_lab.db", help="SQLite file for the prediction log")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("demo", help="simulate data offline and score it")
    d.add_argument("--n", type=int, default=600)
    d.add_argument("--seed", type=int, default=7)
    d.add_argument("--market-noise", type=float, default=0.02)
    d.add_argument("--model-vol-error", type=float, default=0.5)
    d.add_argument("--save", action="store_true", help="also write the simulated rows to --db, so eval/research run offline")
    sub.add_parser("scan", help="log model vs market for open BTC/ETH markets")
    sub.add_parser("settle", help="fill in outcomes for closed markets")
    sub.add_parser("eval", help="score model vs market")
    sub.add_parser("research", help="train/test check (needs pulse-lab[research])")
    a = ap.parse_args(argv)

    if a.cmd == "demo":
        from .demo import simulate
        rows = simulate(a.n, a.seed, a.market_noise, a.model_vol_error)
        if a.save:
            con = store.connect(a.db)
            print(f"Saved {sum(store.add(con, r) for r in rows)} simulated predictions to {a.db}")
        print(evaluate.format_report(evaluate.report(
            [(r["close_ts"], r["model_prob"], r["market_prob"], r["outcome"]) for r in rows])))
        return 0

    con = store.connect(a.db)
    if a.cmd == "scan":
        print(f"Logged {_scan(con)} new predictions to {a.db}")
    elif a.cmd == "settle":
        from .markets import fetch_result
        done = 0
        for t in store.unsettled_tickers(con, time.time() - 300):
            out = fetch_result(t)
            if out is not None:
                done += store.set_outcome(con, t, out)
        print(f"Settled {done} predictions")
    elif a.cmd == "eval":
        print(evaluate.format_report(evaluate.report(store.settled(con))))
    elif a.cmd == "research":
        from .research import compare
        try:
            res = compare(store.settled(con))
        except ImportError:
            print('Install the extra first:  pip install "pulse-lab[research]"'); return 1
        except ValueError as e:
            print(str(e)); return 1
        for k, v in res.items():
            print(f"{k:28s} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
