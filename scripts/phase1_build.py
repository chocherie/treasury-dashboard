#!/usr/bin/env python3
"""
Phase 1: one signal per feature column vs USGG10YR next-day yield change.
- Signal: z-score of daily change (252d rolling, min 126 obs); causal (mean/std end t-1).
- Discrete: z > 0.5 -> +1, z < -0.5 -> -1, else 0.
- Confidence: min(100, |z| * 28)  (|z|~3.5 -> ~100).
- PnL proxy: -signal_t * (y_{t+1} - y_t)  [long duration when signal +1].
- Walk-forward: 8 chronological slices, Sharpe per slice (same rule, no refit).
JSON for web: sanitize NaN/Inf.
"""

from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data" / "processed" / "bbg_treasury_panel.csv"
OUT_JSON = ROOT / "web" / "public" / "data" / "phase1.json"

ROLL = 252
MINP = 126
Z_LONG = 0.5


def _json_safe(obj):
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, (np.floating,)):
        x = float(obj)
        return None if math.isnan(x) or math.isinf(x) else x
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    return obj


def zscore_signal(series: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Daily change z-scores; causal: mean/std of dx use only dx lagged (through t-1)."""
    dx = series.diff()
    m = dx.shift(1).rolling(ROLL, min_periods=MINP).mean()
    sd = dx.shift(1).rolling(ROLL, min_periods=MINP).std()
    z = (dx - m) / sd.replace(0, np.nan)
    sig = pd.Series(0, index=series.index, dtype=float)
    sig = sig.mask(z > Z_LONG, 1.0)
    sig = sig.mask(z < -Z_LONG, -1.0)
    return z, sig


def strategy_returns(signal: pd.Series, y: pd.Series) -> pd.Series:
    dy_fwd = y.shift(-1) - y
    return -signal * dy_fwd


def sharpe(x: pd.Series) -> float | None:
    x = x.dropna()
    if len(x) < 30 or x.std() == 0 or np.isnan(x.std()):
        return None
    return float(np.sqrt(252) * x.mean() / x.std())


def max_drawdown(cum: np.ndarray) -> float:
    if len(cum) == 0:
        return 0.0
    peak = np.maximum.accumulate(cum)
    dd = cum - peak
    return float(dd.min())


def hit_rate(signal: pd.Series, y: pd.Series, strat: pd.Series) -> float | None:
    """Directional: did signal predict sign of -dy_fwd correctly when |signal|=1?"""
    dy_fwd = y.shift(-1) - y
    pred = np.sign(signal)
    actual = np.sign(-dy_fwd)  # bond wins if yield down
    m = (pred != 0) & dy_fwd.notna() & signal.notna()
    if m.sum() == 0:
        return None
    return float((pred[m] == actual[m]).mean())


def walk_forward_sharpes(strat: pd.Series, n_folds: int = 8) -> list[dict]:
    s = strat.dropna()
    if len(s) < n_folds * 30:
        return []
    idx = np.array_split(np.arange(len(s)), n_folds)
    out = []
    for k, block in enumerate(idx):
        chunk = s.iloc[block]
        sh = sharpe(chunk)
        out.append(
            {
                "fold": k + 1,
                "start": str(s.index[block[0]].date()),
                "end": str(s.index[block[-1]].date()),
                "sharpe": sh,
                "n": int(len(chunk)),
            }
        )
    return out


def downsample_equity(
    dates: list,
    *value_rows: list,
    step: int = 5,
) -> tuple[list, ...]:
    """Keep date and parallel value series aligned; always include last point."""
    if not dates:
        return (dates, *tuple([] for _ in value_rows))
    d2: list = []
    rows_out = [[] for _ in value_rows]
    for i in range(0, len(dates), step):
        d2.append(dates[i])
        for j, row in enumerate(value_rows):
            rows_out[j].append(row[i])
    if dates[-1] != d2[-1]:
        d2.append(dates[-1])
        for j, row in enumerate(value_rows):
            rows_out[j].append(row[-1])
    return (d2, *tuple(rows_out))


def buy_hold_returns(y: pd.Series, index: pd.Index) -> pd.Series:
    """Constant long DV01 vs same next-day yield change as strategy: -(y[t+1]-y[t])."""
    dy_fwd = y.shift(-1) - y
    return (-dy_fwd).reindex(index)


def hit_rate_buy_hold(y: pd.Series, index: pd.Index) -> float | None:
    """Share of days when yields fell (long DV01 wins), same rows as strategy."""
    dy_fwd = y.shift(-1) - y
    dy_sub = dy_fwd.reindex(index)
    m = dy_sub.notna()
    if int(m.sum()) == 0:
        return None
    wins = (-dy_sub[m]) > 0
    return float(wins.mean())


def verify_signal_known_before_position(df: pd.DataFrame, feature_col: str) -> None:
    """
    Sanity check: signal at date t does not depend on feature values after t.
    Perturbs all feature observations strictly after t and asserts z/sig unchanged at t.
    """
    col = df[feature_col].astype(float)
    z_full, s_full = zscore_signal(col)
    for _ in range(3):
        t = np.random.choice(df.index[MINP + 5 : -5])
        perturbed = col.copy()
        perturbed.loc[df.index > t] = perturbed.loc[df.index > t] * 1e6 + np.random.randn(len(perturbed.loc[df.index > t]))
        z_p, s_p = zscore_signal(perturbed)
        if pd.notna(z_full.loc[t]):
            assert np.isclose(z_full.loc[t], z_p.loc[t], rtol=1e-9, atol=1e-9), (feature_col, t)
            assert s_full.loc[t] == s_p.loc[t], (feature_col, t)


def run() -> dict:
    df = pd.read_csv(PANEL, parse_dates=["date"], index_col="date").sort_index()
    y = df["USGG10YR"]
    non_target = [c for c in df.columns if c != "USGG10YR"]
    if non_target and os.environ.get("PHASE1_SKIP_CAUSAL_CHECK") != "1":
        np.random.seed(42)
        verify_signal_known_before_position(df, non_target[0])

    tickers_out = []

    for col in df.columns:
        z, sig = zscore_signal(df[col])
        strat = strategy_returns(sig, y)
        valid = strat.notna() & sig.notna() & z.notna()
        # Per-ticker: longest history where feature and strat valid
        sub = strat[valid]
        if len(sub) < 200:
            continue

        cum = sub.cumsum().values
        bh = buy_hold_returns(y, sub.index)
        bh_cum = bh.cumsum().values
        eq_dates = [str(d.date()) for d in sub.index]
        eq_vals = cum.tolist()
        bh_vals = bh_cum.tolist()
        step = max(1, len(eq_dates) // 400)
        eq_d, eq_v, eq_bh = downsample_equity(eq_dates, eq_vals, bh_vals, step=step)

        last_i = z.last_valid_index()
        last_z = float(z.loc[last_i]) if last_i is not None and pd.notna(z.loc[last_i]) else None
        last_sig = int(sig.loc[last_i]) if last_i is not None else 0
        conf = min(100.0, abs(last_z) * 28.0) if last_z is not None and not math.isnan(last_z) else 0.0

        tickers_out.append(
            {
                "id": col,
                "label": col.replace("_", " "),
                "history_start": str(sub.index[0].date()),
                "history_end": str(sub.index[-1].date()),
                "n_days": int(len(sub)),
                "last_date": str(last_i.date()) if last_i is not None else None,
                "last_signal": last_sig,
                "last_z": None if last_z is None or math.isnan(last_z) else round(last_z, 4),
                "last_confidence": round(conf, 1),
                "stats_full": {
                    "sharpe_ann": sharpe(sub),
                    "mean_daily": float(sub.mean()),
                    "std_daily": float(sub.std()),
                    "cum_pnl_yield_pts": float(sub.sum()),
                    "max_drawdown_pts": max_drawdown(cum),
                    "hit_rate": hit_rate(sig, y, strat),
                    "n": int(len(sub)),
                },
                "buy_hold_same_period": {
                    "sharpe_ann": sharpe(bh),
                    "mean_daily": float(bh.mean()),
                    "std_daily": float(bh.std()),
                    "cum_pnl_yield_pts": float(bh.sum()),
                    "max_drawdown_pts": max_drawdown(bh_cum),
                    "hit_rate": hit_rate_buy_hold(y, sub.index),
                    "n": int(len(bh)),
                },
                "walk_forward": walk_forward_sharpes(strat),
                "equity_dates": eq_d,
                "equity_cum": eq_v,
                "equity_buy_hold_cum": eq_bh,
            }
        )

    # Sort by full-sample Sharpe descending (None last)
    def sort_key(x):
        s = x["stats_full"]["sharpe_ann"]
        return (s is None, -(s or -999))

    tickers_out.sort(key=sort_key)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target": "USGG10YR",
        "target_note": "Next-day change in generic US Treasury 10Y yield (close-to-close proxy).",
        "signal_spec": {
            "feature_transform": "First difference of level (daily change).",
            "z_window": ROLL,
            "z_min_periods": MINP,
            "z_causal": "Rolling mean/std use dx shifted by 1 (only past days).",
            "threshold_long_short": Z_LONG,
            "position": "signal at close t applies to yield change from t to t+1.",
            "pnl_proxy": "-signal * (y[t+1]-y[t]); +1 signal = bet on lower yields (duration long).",
            "execution_order": (
                "Signal at t uses feature through x[t] (dx_t) and rolling stats of dx "
                "using only dx up to t-1. PnL uses y[t+1]-y[t]; y[t+1] is not in z_t. "
                "Runtime check: perturbing feature after t does not change z_t/signal_t."
            ),
            "buy_hold_benchmark": (
                "Constant LONG DV01 on the same backtest rows: daily -(y[t+1]-y[t]), "
                "aligned to each factor's valid sample."
            ),
        },
        "tickers": tickers_out,
    }


def main() -> int:
    if not PANEL.exists():
        print(f"Missing panel: {PANEL} — run scripts/clean_bbg_export.py first.", file=sys.stderr)
        return 1
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = run()
    OUT_JSON.write_text(json.dumps(_json_safe(payload), indent=2), encoding="utf-8")
    print(f"Wrote {OUT_JSON} ({len(payload['tickers'])} tickers)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
