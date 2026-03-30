# Quality Scorecard

**Last Updated:** 2026-03-23

## Domain Scores

| Domain | Spec | Code | Tests | Review | Overall | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Data pipeline | B | B | F | Partial | C | Script works; no automated tests yet |
| Signals & backtest | B | B | D | Partial | C+ | Causal timing + B&H benchmark covered in pytest; IS/OOS still open |
| Web dashboard | B | B | F | Partial | C | Timeline equity chart + B&H column; Bombadil not wired |

## Architectural Layers

| Layer | Grade | Notes |
| :--- | :--- | :--- |
| Error handling | D | Minimal in scripts; UI shows load errors |
| Security | N/A | Static read-only dashboard |
| Observability | F | No structured logging |
| Performance | B | Panel size modest |
| CI / Deployment | D | Vercel production deploy + GitHub; no CI tests |
| Documentation | B+ | Scaffold + `docs/user-guide.md` for operators |

## Known Gaps

| Gap | Severity | Tracking |
| :--- | :--- | :--- |
| No pytest / unit tests for merge logic | Medium | TODO Phase 2 |
| Execution-timing audit not encoded | Medium | Feature-side causal check in `phase1_build` + pytest; mixed BBG settlement still manual |
| Walk-forward is 8 equal folds, not rolling OOS | Medium | signals-backtest spec |

## Score History

| Date | Domain | Change |
| :--- | :--- | :--- |
| 2026-03-23 | All | Initial scaffold grades after Phase 1 build |
| 2026-03-23 | Signals & backtest, Web | B&H benchmark, causal timing tests, timeline chart + chart-timeline skill |
| 2026-03-23 | Documentation | Added `docs/user-guide.md` (Bloomberg → UI); README link |
| 2026-03-30 | Deployment | Vercel + root `vercel.json`; prod alias treasury-dashboard-pi.vercel.app |
