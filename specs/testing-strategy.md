# Testing strategy

**Status:** Draft  
**Last Updated:** 2026-03-23

## Goals

- **Scripts:** `pytest` for `clean_bbg_export` merge logic and `phase1_build` outputs (golden JSON shape, no NaN in written JSON).
- **Web:** `vitest` or React Testing Library for critical components (optional); **Bombadil** UI property tests when installed (see `.agents/workflows/verify-ui-properties.md`).
- **Review:** `.agents/workflows/implement-and-verify.md` after material phases.

## Current state

- **Phase 1 timing / benchmark:** `tests/test_phase1_signal_timing.py` (causal feature signal, strategy return identity, B&H = constant long).
- **Still open:** merge/export golden tests, full JSON schema test.

Manual runs:

- `python3 scripts/clean_bbg_export.py`
- `python3 scripts/phase1_build.py`
- `cd web && npm run build`
- `python3 -m pytest tests/test_phase1_signal_timing.py`

## Python

- Place tests under `tests/` (create when first test lands).
- Use small fixture CSV/Excel slices committed under `tests/fixtures/` if needed.

## Web

- Prefer testing pure formatters and JSON types in TS before E2E.
- Bombadil requires separate install; document URL in spec when CI adds it.
