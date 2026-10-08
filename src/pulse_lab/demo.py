"""Offline demo data, so the whole lab runs with no internet and no accounts.

It simulates price paths, a "market" whose odds are the true probability plus noise,
and a model that sees a noisier volatility than the truth. Change the noise levels
and watch which one wins: that is the core experiment of this lab.
"""
from __future__ import annotations

import math
import random
from typing import List

from .model import prob_above


def simulate(n: int = 600, seed: int = 7, market_noise: float = 0.02, model_vol_error: float = 0.5) -> List[dict]:
    rng = random.Random(seed)
    rows, t0 = [], 1_700_000_000.0
    for i in range(n):
        spot = 60_000 * math.exp(rng.gauss(0, 0.05))
        true_vol = rng.uniform(0.35, 0.75)
        hours = rng.uniform(1, 8)
        strike = round(spot * math.exp(rng.gauss(0, 0.02)), -2)
        p_true = prob_above(spot, strike, true_vol, hours)
        sig = true_vol * math.sqrt(hours / (24 * 365))
        end = spot * math.exp(-0.5 * sig * sig + sig * rng.gauss(0, 1))
        outcome = 1 if end > strike else 0
        market = min(0.99, max(0.01, p_true + rng.gauss(0, market_noise)))
        model_vol = true_vol * math.exp(rng.gauss(0, model_vol_error))
        model = prob_above(spot, strike, model_vol, hours)
        close = t0 + i * 3600
        rows.append({"pred_id": f"DEMO-{i}", "ticker": f"DEMO-BTC-T{int(strike)}-{i}", "asset": "BTC",
                     "created_ts": close - hours * 3600, "close_ts": close,
                     "model_prob": round(model, 4), "market_prob": round(market, 4),
                     "spot": spot, "strike": strike, "vol": round(model_vol, 4), "hours": round(hours, 3),
                     "outcome": outcome})
    return rows
