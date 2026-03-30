# Spec: Data pipeline (Bloomberg → panel CSV)

## Overview

Convert a Bloomberg Excel sheet with **wide BDH spills** (three columns per series: Date, Value, spacer) into one **date-indexed** panel aligned to **USGG10YR** trading days.

## Inputs

- **File:** Excel `.xlsx`, default path `data/upload/BBG_23Mar2026.xlsx` (overridable via CLI arg).
- **Layout:** Row 0–1 date range; row 2–3 headers; row 4+ data blocks per series.

## Outputs

- `data/processed/bbg_treasury_panel.csv` — index column `date`, one column per ticker (sanitized names).
- `data/processed/bbg_treasury_panel_meta.json` — source path, column list, missing % per column.

## Behavior

1. Parse each block’s (date, value) pairs; drop duplicate dates per series (`keep=last`).
2. Outer-join all series on `date`; **drop rows where `USGG10YR` is NaN** (removes holiday orphans).
3. Ticker names: strip ` Index`, ` Govt`, ` Curncy` suffixes for column headers.

## CLI

```bash
python3 scripts/clean_bbg_export.py [path/to/file.xlsx]
```

## Error handling

- Missing input file → exit non-zero, stderr message.

## Design decisions

- **USGG10YR as calendar anchor** matches Treasury-focused backtests; DXY-only days are excluded.
