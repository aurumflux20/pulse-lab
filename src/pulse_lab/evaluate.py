"""Scoring. The Brier score is the mean of (probability - outcome)^2. Lower is better.

The market's own price is the baseline. A model is only interesting if it beats it.
"""
from __future__ import annotations

from typing import Dict, List, Sequence, Tuple


def brier(probs: Sequence[float], outcomes: Sequence[int]) -> float:
    if not probs:
        raise ValueError("no predictions to score")
    return sum((p - o) ** 2 for p, o in zip(probs, outcomes)) / len(probs)


def report(rows: Sequence[Tuple[float, float, float, int]]) -> Dict:
    """rows = (close_ts, model_prob, market_prob, outcome)."""
    n = len(rows)
    if n == 0:
        return {"n": 0}
    model = [r[1] for r in rows]
    market = [r[2] for r in rows]
    out = [int(r[3]) for r in rows]
    bm, bk = brier(model, out), brier(market, out)
    bins: List[Tuple[float, int, float, float]] = []
    for lo in (0.0, 0.2, 0.4, 0.6, 0.8):
        sel = [(p, o) for p, o in zip(model, out) if lo <= p < lo + 0.2 or (lo == 0.8 and p == 1.0)]
        if sel:
            bins.append((lo, len(sel), sum(p for p, _ in sel) / len(sel), sum(o for _, o in sel) / len(sel)))
    return {"n": n, "brier_model": bm, "brier_market": bk,
            "skill_vs_market": (1 - bm / bk) if bk > 0 else 0.0, "calibration": bins}


def format_report(ev: Dict) -> str:
    if ev.get("n", 0) == 0:
        return "No settled predictions yet. They settle as markets close."
    if ev["n"] < 100:
        verdict = "Too few to judge yet (aim for 100+; nearby strikes move together)."
    elif ev["brier_model"] < ev["brier_market"]:
        verdict = "The model beat the market's own odds on this sample."
    else:
        verdict = "The market's odds beat the model. That is the usual result, and a real finding."
    lines = [f"Settled predictions: {ev['n']}",
             f"Brier score (lower is better): model {ev['brier_model']:.4f} | market {ev['brier_market']:.4f}",
             f"Skill vs market: {ev['skill_vs_market']:+.1%}", verdict, "",
             "Calibration (model said -> what actually happened):"]
    for lo, cnt, avg, freq in ev["calibration"]:
        lines.append(f"  {lo:.0%}-{lo + 0.2:.0%}: said {avg:.0%}, happened {freq:.0%} (n={cnt})")
    return "\n".join(lines)
