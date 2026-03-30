---
name: chart-timeline
description: >-
  Require time-based charts (sparklines, equity curves, backtests) to expose a
  real date or time axis—never anonymous index-only lines. Use when building or
  reviewing financial dashboards, trading UIs, or any chart where the x-axis is
  time.
---

# Charts must show a timeline

## Rule

Any chart whose x-dimension is **time** must make that explicit:

1. **Data:** pass parallel `dates[]` (ISO `YYYY-MM-DD` or full ISO timestamps) alongside `values[]`; keep them aligned after downsampling.
2. **Rendering:** map x-positions from parsed dates (linear time scale), not only from array index. Index-only spacing hides irregular gaps (holidays, missing rows) and confuses readers.
3. **Axis labels:** show at least **start**, **end**, and **middle** tick labels (or a readable tick strategy for very long ranges). Use short month+year or locale-appropriate compact labels.
4. **A11y:** set `role="img"` and a concise `aria-label` describing what time range and series are shown.
5. **Multiple series:** share the same time base and y-scale rules (e.g. min/max across series for comparable cumulative curves). Differentiate with stroke, dash, and a small text legend under the chart.

## Checklist before shipping

- [ ] Downsampled points still carry dates; downsampling steps apply to all series in lockstep.
- [ ] Gradient or pattern IDs are unique per chart instance (e.g. React `useId`) when SVG `url(#id)` is used.
- [ ] Tooltip or axis text uses the same date source as the path (no off-by-one vs CSV).

## Reference in this repo

- `web/src/App.tsx` — `EquityTimelineChart`: cumulative strategy vs buy-and-hold with `equity_dates` + `equity_cum` / `equity_buy_hold_cum`.
- `scripts/phase1_build.py` — `downsample_equity` keeps date and parallel value arrays aligned.
