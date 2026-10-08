"""Offline tests: no network, no keys."""
import math
from datetime import datetime, timedelta, timezone

import pulse_lab
from pulse_lab import cli, evaluate, markets, model, store
from pulse_lab.demo import simulate


def test_prob_above_is_half_at_the_money_and_monotonic():
    p_atm = model.prob_above(100, 100, 0.5, 24)
    assert 0.48 < p_atm < 0.5          # slightly under 0.5: the -sigma^2/2 drift term
    assert model.prob_above(110, 100, 0.5, 24) > p_atm > model.prob_above(90, 100, 0.5, 24)
    assert model.prob_above(100, 100, 0.0, 24) is None
    assert model.prob_above(1e9, 1, 0.5, 24) == 0.99     # never claims certainty


def test_realised_vol_recovers_a_known_volatility():
    import random
    rng = random.Random(1)
    step_ms, annual = 3_600_000, 0.6
    per_step = annual / math.sqrt(24 * 365)
    pts, p = [], 100.0
    for i in range(2000):
        pts.append((i * step_ms, p))
        p *= math.exp(rng.gauss(0, per_step))
    v = model.realised_vol(pts)
    assert abs(v - annual) < 0.05


def test_parse_market_reads_both_price_formats_and_rejects_junk():
    now = datetime(2026, 10, 8, tzinfo=timezone.utc)
    close = (now + timedelta(hours=5)).isoformat().replace("+00:00", "Z")
    m = markets.parse_market({"ticker": "KXBTCD-26OCT08-T62000", "yes_ask_dollars": "0.56",
                              "yes_bid_dollars": "0.52", "close_time": close}, now)
    assert m["asset"] == "BTC" and m["strike"] == 62000 and m["yes_ask"] == 56
    assert abs(m["market_prob"] - 0.54) < 1e-9 and abs(m["hours"] - 5) < 1e-6
    old = markets.parse_market({"ticker": "KXETHD-X-T2500", "yes_ask": 40, "yes_bid": 38, "close_time": close}, now)
    assert old["asset"] == "ETH" and old["yes_ask"] == 40
    assert markets.parse_market({"ticker": "KXNBA-GAME", "yes_ask": 50, "close_time": close}, now) is None
    assert markets.parse_market({"ticker": "KXBTCD-X-T1", "yes_ask": 0, "close_time": close}, now) is None


def test_store_roundtrip_and_settle(tmp_path):
    con = store.connect(str(tmp_path / "t.db"))
    row = {"pred_id": "A|1", "ticker": "A", "asset": "BTC", "created_ts": 1, "close_ts": 10,
           "model_prob": 0.7, "market_prob": 0.6, "spot": 1, "strike": 1, "vol": 0.5, "hours": 1, "outcome": None}
    assert store.add(con, row) and not store.add(con, row)       # same id is logged once
    assert store.unsettled_tickers(con, 100) == ["A"]
    assert store.set_outcome(con, "A", 1) == 1
    assert store.settled(con) == [(10.0, 0.7, 0.6, 1)]


def test_brier_and_report():
    assert evaluate.brier([1.0, 0.0], [1, 0]) == 0.0
    assert evaluate.brier([0.5], [1]) == 0.25
    ev = evaluate.report([(1, 0.9, 0.5, 1), (2, 0.1, 0.5, 0)])
    assert ev["brier_model"] < ev["brier_market"] and ev["n"] == 2
    assert "Too few" in evaluate.format_report(ev)
    assert evaluate.report([]) == {"n": 0}


def test_demo_market_wins_when_model_is_noisier():
    rows = simulate(n=800, seed=3, market_noise=0.01, model_vol_error=0.6)
    ev = evaluate.report([(r["close_ts"], r["model_prob"], r["market_prob"], r["outcome"]) for r in rows])
    assert ev["brier_market"] < ev["brier_model"]


def test_cli_demo_runs_offline(capsys):
    assert cli.main(["demo", "--n", "200"]) == 0
    assert "Brier score" in capsys.readouterr().out


def test_no_trading_or_secret_code_in_package():
    import pathlib
    src = "".join(p.read_text() for p in pathlib.Path(pulse_lab.__file__).parent.glob("*.py")).lower()
    for banned in ("private_key", "api_key", "telegram", "supabase", "portfolio/orders", "requests.post",
                   ".post(", "live_trading", "execute_live", "kalshi-access"):
        assert banned not in src, banned


def test_demo_defaults_show_the_usual_result_and_flip_when_the_market_is_noisy():
    def skill(**kw):
        rows = simulate(**kw)
        return evaluate.report([(r["close_ts"], r["model_prob"], r["market_prob"], r["outcome"]) for r in rows])["skill_vs_market"]
    assert skill() < 0
    assert skill(market_noise=0.10, model_vol_error=0.05) > 0
