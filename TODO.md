# Treasury dashboard — implementation plan

**Current Phase:** 2 planning  
**Last Updated:** 2026-03-23

## Quick status

| Phase | Status | Notes |
| :--- | :--- | :--- |
| Phase 1: Single-factor signals + web | Complete | Panel, phase1 JSON, Vite UI |
| Phase 2: Tests + rigor | Not started | pytest, IS/OOS, costs |
| Phase 3: Composite / regime | Planned | — |

---

## Phase 1 — COMPLETE

- [x] BDH paste TSV + Excel workflow documented
- [x] `clean_bbg_export.py` + `bbg_treasury_panel.csv`
- [x] `phase1_build.py` + `phase1.json`
- [x] `web/` dashboard (table + detail + methodology)
- [x] `docs/user-guide.md` — comprehensive operator guide
- [x] Project scaffold (this TODO, specs, docs, rules, workflows)

---

## Phase 2: Tests and backtest rigor

- [ ] `tests/test_clean_bbg_export.py` — merge + USGG10YR anchor
- [x] `tests/test_phase1_signal_timing.py` — causal feature signal vs future data; B&H = constant long leg
- [ ] `tests/test_phase1_build.py` — JSON schema / no NaN / known Sharpe sign smoke
- [ ] Document IS/OOS window in spec; implement rolling or expanding OOS Sharpe
- [ ] Optional: transaction cost knob in `phase1_build.py`
- [ ] Update `docs/quality.md` and `specs/README.md` verification when tests land

### Phase 2 verification

- [ ] `pytest` passes
- [ ] `cd web && npm run build` passes
- [ ] Run implement-and-verify workflow for review

---

## Phase 3: Composite signal (future)

- [ ] Majority vote or walk-forward ensemble across tickers
- [ ] Event-day filters (ECO calendar)

---

## Decision log

| Date | Decision |
| :--- | :--- |
| 2026-03-23 | Scaffold retrofitted; specs split data-pipeline / signals-backtest / web-dashboard |
