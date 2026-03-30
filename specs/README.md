# Specifications index

| Spec | Code location | Purpose | Status | Verified |
| :--- | :--- | :--- | :--- | :--- |
| [data-pipeline.md](./data-pipeline.md) | `scripts/clean_bbg_export.py` | Bloomberg wide BDH → single-date CSV panel | Implemented | Partial |
| [signals-backtest.md](./signals-backtest.md) | `scripts/phase1_build.py` | Per-ticker z-signals, PnL vs USGG10YR, B&H, JSON | Implemented | Partial |
| [web-dashboard.md](./web-dashboard.md) | `web/src/`, `vercel.json` | Phase 1 UI + Vercel static deploy | Implemented | Partial |
| [testing-strategy.md](./testing-strategy.md) | `tests/test_phase1_signal_timing.py` | How we test (target state) | Draft | Partial |

See status/verified legends in the project-scaffold skill (`Draft` / `Implemented` / `Verified Yes|Partial|No`).
