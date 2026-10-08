"""Does the model know anything the market doesn't? A proper train/test check.

Compares, on a TEST set split by close time:
  1. market price alone (the baseline)
  2. the volatility model alone
  3. logistic regression on the market price
  4. logistic regression on the market price + the model
If (4) does not beat (3), the model adds no information beyond the market.
Needs the optional extra:  pip install "pulse-lab[research]"
"""
from __future__ import annotations

from typing import Dict, Sequence, Tuple

EPS = 1e-4


def compare(rows: Sequence[Tuple[float, float, float, int]], test_frac: float = 0.3) -> Dict:
    import numpy as np
    from sklearn.linear_model import LogisticRegression

    d = np.array(sorted(rows), dtype=float)
    close, model_p, market_p, y = d[:, 0], d[:, 1], d[:, 2], d[:, 3].astype(int)
    cutoff = np.quantile(close, 1 - test_frac)
    tr, te = close < cutoff, close >= cutoff
    if tr.sum() < 50 or te.sum() < 50 or len(set(y[tr])) < 2:
        raise ValueError("not enough data on each side of the split; collect more")

    def logit(p):
        p = np.clip(p, EPS, 1 - EPS)
        return np.log(p / (1 - p))

    def brier(p, yy):
        return float(np.mean((p - yy) ** 2))

    x1 = logit(market_p).reshape(-1, 1)
    x2 = np.column_stack([logit(market_p), logit(model_p)])
    lr1 = LogisticRegression().fit(x1[tr], y[tr])
    lr2 = LogisticRegression().fit(x2[tr], y[tr])
    res = {
        "market_alone": brier(market_p[te], y[te]),
        "model_alone": brier(model_p[te], y[te]),
        "logreg_market": brier(lr1.predict_proba(x1[te])[:, 1], y[te]),
        "logreg_market_plus_model": brier(lr2.predict_proba(x2[te])[:, 1], y[te]),
        "train": int(tr.sum()), "test": int(te.sum()),
        "weights": [float(w) for w in lr2.coef_[0]],
    }
    res["model_adds_information"] = (res["logreg_market"] - res["logreg_market_plus_model"]) > 0.001
    return res
