# pulse-lab

A forecasting lab built around one question:

> **Can a simple math model predict a price better than a prediction market already does?**

Prediction markets (like Kalshi) post odds such as "56% chance Bitcoin closes above $62,000 today".
pulse-lab computes its own probability for the same question, writes both numbers down, waits for the
answer, and scores who was closer. Most of the time the market wins. Finding out *when* it doesn't,
and why, is the project.

**pulse-lab only reads and scores.** It has no code that can place a bet, log into an account, or move money,
and it needs no API keys. A test in `tests/` fails if trading or key-handling code is ever added.

## Install

```bash
pip install pulse-lab-0.1.0-py3-none-any.whl          # from the dist/ folder
pip install "pulse-lab-0.1.0-py3-none-any.whl[research]"  # adds numpy + scikit-learn for the ML step
```
Or from the source folder: `pip install -e ".[research,test]"`.

## Try it with no internet first

```bash
pulse-lab demo                                             # the market usually wins
pulse-lab demo --market-noise 0.10 --model-vol-error 0.05   # now the model should win. Why?
```
The demo simulates prices, a market whose odds are the true probability plus some noise, and a model that
measures volatility a bit wrong. Changing the two noise levels changes who wins.

To try the machine-learning step offline too:
```bash
pulse-lab --db demo.db demo --save
pulse-lab --db demo.db research
```

## Run it on real public data

```bash
pulse-lab scan       # logs model vs market for open daily BTC/ETH markets (read-only)
pulse-lab settle     # later: fills in what actually happened
pulse-lab eval       # scores both with the Brier score
pulse-lab research   # machine-learning check: does the model add anything the market didn't know?
```
`scan` skips strikes the market already prices below 5% or above 95%, since those teach nothing, and markets whose bid-ask gap is wider than 10 cents, since their "price" is not a real consensus. Run `scan` a few times a day for a couple of weeks; you need 100+ settled predictions before the
scores mean much. Everything is stored in `pulse_lab.db` (SQLite) in the current folder.

## The ideas inside

| File | What it teaches |
|---|---|
| `model.py` | The lognormal price model (the same maths as option pricing) and measuring volatility from prices |
| `evaluate.py` | The Brier score and calibration: "when the model says 70%, does it happen 70% of the time?" |
| `research.py` | A fair ML test: split by time, logistic regression, compare against the market baseline |
| `demo.py` | A simulator, so you can test ideas without waiting for real markets |

## Ideas to build next

- Use a better volatility estimate (exponentially weighted, or a GARCH model) and see if the Brier score improves.
- Add features to the logistic regression: hours to close, distance of the strike from the price.
- Plot a calibration chart with matplotlib.
- Try another asset with free price data.

## Honest limits

- Predictions on nearby strikes of the same day move together, so the real sample is smaller than the row count.
- The model assumes a market resolves YES when the price ends **above** the strike. Check each series' rules.
- This is a science project, not financial advice.

MIT licensed: use it, change it, share it.
