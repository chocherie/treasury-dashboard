#!/usr/bin/env python3
"""Merge Bloomberg Excel BDH wide spill (3-col blocks) into one date-indexed panel."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

# Row layout from BDH paste template: rows 0-1 = date range, 2-3 = headers, 4+ = data
HEADER_TICKER_ROW = 3
DATA_START_ROW = 4
BLOCK_WIDTH = 3


def ticker_to_colname(ticker: str) -> str:
    ticker = str(ticker).strip()
    for suffix in (" Index", " Govt", " Curncy"):
        if ticker.endswith(suffix):
            return ticker[: -len(suffix)].replace(" ", "_")
    return re.sub(r"\W+", "_", ticker)


def load_bbg_wide(path: Path) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name=0, header=None)
    tickers = raw.iloc[HEADER_TICKER_ROW]
    ncols = raw.shape[1]
    blocks = list(range(0, ncols, BLOCK_WIDTH))

    series_list: dict[str, pd.Series] = {}
    for c in blocks:
        if c + 1 >= ncols:
            break
        tcell = tickers.iloc[c]
        if pd.isna(tcell):
            continue
        name = ticker_to_colname(tcell)
        sub = raw.iloc[DATA_START_ROW:, [c, c + 1]].copy()
        sub.columns = ["date", "value"]
        sub["date"] = pd.to_datetime(sub["date"], errors="coerce")
        sub["value"] = pd.to_numeric(sub["value"], errors="coerce")
        sub = sub.dropna(subset=["date"]).dropna(subset=["value"])
        sub["date"] = sub["date"].dt.normalize()
        # Same calendar day duplicates: keep last (latest pull)
        sub = sub.drop_duplicates(subset=["date"], keep="last")
        s = sub.set_index("date")["value"]
        s.name = name
        if name in series_list:
            name = f"{name}_{c}"
        series_list[name] = s

    panel = pd.DataFrame(series_list)
    panel = panel.sort_index()
    panel = panel[~panel.index.duplicated(keep="last")]
    # Drop dates with no Treasury generic 10y (orphan rows from other calendars, e.g. holidays)
    anchor = "USGG10YR" if "USGG10YR" in panel.columns else panel.columns[0]
    panel = panel[panel[anchor].notna()]
    return panel


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    upload = root / "data" / "upload" / "BBG_23Mar2026.xlsx"
    out_dir = root / "data" / "processed"
    out_csv = out_dir / "bbg_treasury_panel.csv"
    out_meta = out_dir / "bbg_treasury_panel_meta.json"

    if len(sys.argv) > 1:
        upload = Path(sys.argv[1])
    if not upload.exists():
        print(f"Missing input: {upload}", file=sys.stderr)
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    panel = load_bbg_wide(upload)

    panel.to_csv(out_csv)

    meta = {
        "source_xlsx": str(upload.resolve()),
        "rows": int(len(panel)),
        "date_start": str(panel.index.min().date()),
        "date_end": str(panel.index.max().date()),
        "columns": list(panel.columns),
        "missing_pct": {c: float(panel[c].isna().mean()) for c in panel.columns},
    }
    out_meta.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Wrote {out_csv} ({len(panel)} rows x {len(panel.columns)} cols)")
    print(f"Wrote {out_meta}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
