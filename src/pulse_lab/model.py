"""The price model: how likely is a price to end above a level (the "strike") by a deadline?

It uses a driftless lognormal model, the same idea behind option pricing:
    sigma_t = vol * sqrt(hours / hours_per_year)
    P(above) = Phi( (ln(spot / strike) - sigma_t^2 / 2) / sigma_t )
where Phi is the normal cumulative distribution and vol is the annualised
volatility measured from recent prices.
"""
from __future__ import annotations

import math
import statistics
from typing import Iterable, Optional, Sequence, Tuple

HOURS_PER_YEAR = 24 * 365
COINGECKO_IDS = {"BTC": "bitcoin", "ETH": "ethereum"}


def norm_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def prob_above(spot: float, strike: float, annual_vol: float, hours: float) -> Optional[float]:
    """Probability that the price ends above `strike` after `hours`. Clipped to [0.01, 0.99]."""
    if spot <= 0 or strike <= 0 or annual_vol <= 0 or hours <= 0:
        return None
    sig = annual_vol * math.sqrt(hours / HOURS_PER_YEAR)
    d2 = (math.log(spot / strike) - 0.5 * sig * sig) / sig
    return min(0.99, max(0.01, norm_cdf(d2)))


def realised_vol(points: Sequence[Tuple[float, float]]) -> Optional[float]:
    """Annualised volatility from (timestamp_ms, price) points sampled at a regular step."""
    pts = [(t, p) for t, p in points if p and p > 0]
    if len(pts) < 25:
        return None
    rets = [math.log(b[1] / a[1]) for a, b in zip(pts, pts[1:])]
    step_h = (pts[-1][0] - pts[0][0]) / (len(pts) - 1) / 3_600_000
    if step_h <= 0 or len(rets) < 24:
        return None
    return statistics.pstdev(rets) * math.sqrt(HOURS_PER_YEAR / step_h)


def fetch_spot_and_vol(asset: str, session=None) -> Tuple[Optional[float], Optional[float]]:
    """Current price and volatility from about 3 days of free CoinGecko prices (no key needed)."""
    import requests
    cg = COINGECKO_IDS.get(asset.upper())
    if not cg:
        return None, None
    s = session or requests
    r = s.get(f"https://api.coingecko.com/api/v3/coins/{cg}/market_chart",
              params={"vs_currency": "usd", "days": "3"}, timeout=10)
    r.raise_for_status()
    pts = [(p[0], p[1]) for p in r.json().get("prices", []) if p and p[1]]
    vol = realised_vol(pts)
    return (pts[-1][1] if pts else None), vol
