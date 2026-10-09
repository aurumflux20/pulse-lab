# Pulse Lab

**A forecasting and machine-learning lab that tests whether a mathematical model can predict real-world prices better than a prediction market.**

## Project description

Prediction markets put a live probability on questions like "Will Bitcoin close above $62,000 today?" Pulse Lab builds its own answer to each question from a pricing model. It records both forecasts side by side, waits for the real outcome, and scores which one was more accurate. Over hundreds of questions this shows whether the model has any real skill, how well calibrated it is, and whether machine learning can improve it.

The project is read-only. It uses free public data, needs no accounts or API keys, and contains no code that can trade or move money.

## What Pulse Lab can do

| Capability | What it means |
|---|---|
| **Price-probability model** | Calculates the chance a price ends above a level by a deadline, using a lognormal model, the same mathematics used to price options. |
| **Live volatility measurement** | Measures how much Bitcoin and Ethereum are moving from the last three days of public price data. |
| **Live market reader** | Reads open Bitcoin and Ethereum prediction questions and their current odds from Kalshi's public data. It skips illiquid or near-certain questions. |
| **Forecast log** | Saves every forecast, model and market side by side, in a local SQLite database, then fills in the real outcome once each question closes. |
| **Accuracy scoring** | Scores both forecasters with the Brier score, the standard measure for probability forecasts, and reports the model's skill relative to the market. |
| **Calibration report** | Checks whether "70%" really happens about 70% of the time, bucket by bucket. |
| **Machine-learning test** | Trains a logistic regression on older questions and tests it on newer ones. This answers whether the model adds information the market didn't already have. |
| **Offline simulator** | Generates realistic synthetic markets, so every feature works with no internet. Adjustable noise settings let you see when a model beats the market and when it can't. |
| **Command-line tool** | One command, `pulse-lab`, with demo, scan, settle, eval and research steps. |
| **Tested and packaged** | Ships as a standard pip-installable Python package with an automated test suite. |

## Skills it demonstrates

Probability and statistics, financial modelling, data collection from live APIs, data storage, forecast evaluation, supervised machine learning with a fair train/test split, simulation, and software packaging and testing.

## Tech

Python 3.9+, `requests`, SQLite, and optionally NumPy and scikit-learn for the machine-learning step. MIT licensed.

## Ideas to extend it

- A smarter volatility model (EWMA or GARCH).
- More machine-learning features: time to close, distance from the current price, recent momentum.
- Charts: a calibration plot and a running accuracy curve.
- More assets with free public price data.
