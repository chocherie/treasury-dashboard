# Spec: Signals & Phase 1 backtest

## Overview

For each numeric column in `bbg_treasury_panel.csv`, build a **daily** causal signal from **z-score of first differences**, backtest against **next-day change in USGG10YR**, emit **`web/public/data/phase1.json`** for the UI.

## Signal definition

- `dx_t = x_t - x_{t-1}`; rolling mean/std of `dx` with window **252**, **min_periods 126**, computed with `dx.shift(1)` so statistics use only prior days.
- `z_t = (dx_t - mean_t) / std_t`
- Discrete: `z > 0.5` → +1, `z < -0.5` → -1, else 0 (long duration interpretation vs 10y).
- **Confidence:** `min(100, |z| * 28)`.

## PnL proxy

- `r_t = -signal_t * (y_{t+1} - y_t)` where `y` is `USGG10YR`.

## Execution timing (no look-ahead on the feature)

- At date `t`, `z_t` uses `dx_t = x_t - x_{t-1}` and rolling mean/std of `dx` with **`dx` shifted by one day**, so the mean/std at `t` depend only on `dx` through `t-1`.
- `y_{t+1}` is **not** used to compute `signal_t`; it only enters the **next-day** PnL leg.
- **Runtime:** `phase1_build.py` optionally perturbs all feature values strictly after `t` and asserts `z_t`/`signal_t` unchanged (sample column; set `PHASE1_SKIP_CAUSAL_CHECK=1` to skip). **Tests:** `tests/test_phase1_signal_timing.py`.

## Buy-and-hold benchmark

- On the **same backtest rows** as each factor (same `sub` index), constant **long DV01**: daily `-(y_{t+1}-y_t)`.
- JSON: `buy_hold_same_period` (Sharpe, cum, max DD, hit rate, n) and downsampled `equity_buy_hold_cum` aligned with `equity_dates` / `equity_cum`.

## Outputs (JSON)

- Per ticker: `last_signal`, `last_z`, `last_confidence`, `stats_full` (Sharpe, hit rate, cum sum, max DD, n), `buy_hold_same_period`, `walk_forward` (8 chronological Sharpe folds), downsampled `equity_dates`, `equity_cum`, `equity_buy_hold_cum`.

## CLI

```bash
python3 scripts/phase1_build.py
```

## Limitations (documented for users)

- Not duration-hedged cash PnL; no transaction costs.
- Mixed settlement times across Bloomberg fields → execution-timing audit recommended before live use.

## Future

- IS/OOS walk-forward with overfit ratio; optional weekly rebalance / min-hold per `AGENTS.md` preferences.
