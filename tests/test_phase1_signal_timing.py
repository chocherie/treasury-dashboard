"""Confirm Phase 1 signals at t do not use feature data after t (no look-ahead on the feature)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_phase1():
    path = ROOT / "scripts" / "phase1_build.py"
    spec = importlib.util.spec_from_file_location("phase1_build", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


phase1 = _load_phase1()


def test_z_invariant_to_future_feature_values():
    """Changing x after t must not change z or discrete signal at t."""
    rng = np.random.default_rng(0)
    idx = pd.bdate_range("2010-01-04", periods=800, freq="C")
    x = pd.Series(rng.normal(0, 1, size=len(idx)).cumsum() + 100, index=idx, name="feat")
    df = pd.DataFrame({"feat": x})
    z0, s0 = phase1.zscore_signal(df["feat"])
    for _ in range(20):
        t = rng.choice(df.index[phase1.MINP + 10 : -10])
        alt = df["feat"].copy()
        alt.loc[df.index > t] = alt.loc[df.index > t] * 1e3 + rng.normal(size=int((df.index > t).sum()))
        z1, s1 = phase1.zscore_signal(alt)
        if pd.notna(z0.loc[t]):
            assert np.isclose(z0.loc[t], z1.loc[t], rtol=1e-9, atol=1e-9)
            assert float(s0.loc[t]) == float(s1.loc[t])


def test_position_uses_only_future_yield_change():
    """Strategy return at t uses y[t+1]-y[t]; must not require y beyond t+1 for that row."""
    idx = pd.bdate_range("2015-01-05", periods=120, freq="C")
    y = pd.Series(np.linspace(2.0, 2.5, len(idx)), index=idx)
    sig = pd.Series([0, 1, -1, 0, 1] * 24, index=idx, dtype=float)
    r = phase1.strategy_returns(sig, y)
    dy = y.shift(-1) - y
    manual = -sig * dy
    pd.testing.assert_series_equal(r, manual, check_names=False)


def test_buy_hold_matches_constant_long_signal():
    idx = pd.bdate_range("2018-01-02", periods=100, freq="C")
    rng = np.random.default_rng(1)
    y = pd.Series(rng.normal(0, 0.05, len(idx)).cumsum() + 3, index=idx)
    ones = pd.Series(1.0, index=idx)
    strat = phase1.strategy_returns(ones, y)
    bh = phase1.buy_hold_returns(y, idx)
    pd.testing.assert_series_equal(strat, bh, check_names=False)
