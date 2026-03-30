# Spec: Web dashboard (Phase 1)

## Overview

Static **Vite + React + TypeScript** app that loads `public/data/phase1.json` and displays per-ticker signals, confidence, and backtest statistics.

## Data contract

- **GET** relative URL `${BASE}data/phase1.json` (Vite `base: './'` for static hosting).
- JSON must contain no raw `NaN`/`Infinity` (Python sanitizes before write).

## UI requirements

1. **Table:** all tickers sorted by full-sample Sharpe (desc); columns include signal label (LONG DV01 / SHORT DV01 / FLAT), confidence, z, strategy Sharpe, **buy-and-hold Sharpe (same period)**, hit rate, cum PnL proxy, max DD, n, history range.
2. **Detail pane:** on row select — **timeline chart** of cumulative PnL (date-scaled x-axis, start/mid/end labels) with **strategy vs buy-and-hold (long DV01)** overlay where JSON provides `equity_buy_hold_cum`; walk-forward Sharpe chips; latest signal recap; optional side-by-side Sharpe / hit / cum vs B&H.
3. **Methodology:** render `signal_spec` key-value list from JSON (includes `execution_order`, `buy_hold_benchmark`).
4. **Footer:** disclaimer (not advice; yield proxy).

## Design skill

- Project skill **chart-timeline** (`.cursor/skills/chart-timeline/SKILL.md`): time series charts must carry dates and visible axis labels, not index-only sparklines.

## Visual design

- Distinct from generic “AI slant” UI: custom typography (DM Serif Display + JetBrains Mono), dark theme, copper/patina/ember accents (see `src/index.css`).

## Build

```bash
cd web && npm install && npm run dev
cd web && npm run build   # output web/dist
```

## Future

- Filters, composite signal phase, export CSV from UI.
