# Treasury dashboard — user guide

**Last updated:** 2026-03-23  

This guide is for **analysts and operators** who pull Bloomberg data, refresh the panel, and read the Phase 1 web dashboard. For system design and code locations, see [`architecture.md`](./architecture.md) and [`specs/README.md`](../specs/README.md).

---

## Table of contents

1. [What this project does](#1-what-this-project-does)
2. [What you need installed](#2-what-you-need-installed)
3. [End-to-end workflow](#3-end-to-end-workflow)
4. [Step A — Bloomberg Excel BDH export](#4-step-a--bloomberg-excel-bdh-export)
5. [Step B — Build the daily panel CSV](#5-step-b--build-the-daily-panel-csv)
6. [Step C — Build signals and `phase1.json`](#6-step-c--build-signals-and-phase1json)
7. [Step D — Run or publish the web dashboard](#7-step-d--run-or-publish-the-web-dashboard)
8. [Using the dashboard](#8-using-the-dashboard)
9. [How to read the statistics](#9-how-to-read-the-statistics)
10. [Execution timing and limitations](#10-execution-timing-and-limitations)
11. [Troubleshooting](#11-troubleshooting)
12. [Where to go next](#12-where-to-go-next)

---

## 1. What this project does

The Treasury dashboard is a **research stack** that:

1. Takes a **Bloomberg Excel** workbook with historical series (BDH layout).
2. Merges those series into one **daily panel** CSV, aligned to **US generic 10-year** (`USGG10YR`) trading days.
3. For **each column** in that panel (except the anchor logic, which still includes all columns in the file), builds a **simple daily signal** from the **z-score of day-over-day changes** in that series.
4. Backtests each signal against the **next business day’s change in USGG10YR** (a yield **change**, in the same units as your panel).
5. Writes **`web/public/data/phase1.json`** and shows results in a **static React** app: sortable table, per-ticker detail, cumulative PnL chart with a **date axis**, and a **buy-and-hold long DV01** comparison on the **same dates** as each factor’s backtest.

**Important:** Outputs are **not investment advice**. PnL is a **yield-change proxy**, not cash with costs or duration hedging. See the in-app footer and [Section 10](#10-execution-timing-and-limitations).

---

## 2. What you need installed

| Requirement | Purpose |
| :--- | :--- |
| **Bloomberg Terminal** + Excel | Pull BDH history into a spreadsheet |
| **Python 3** + packages | `pip install pandas numpy openpyxl` |
| **Node.js** (LTS) + npm | Build and run the `web/` app |

You do **not** need API keys or a server for Phase 1: the site reads a local JSON file.

---

## 3. End-to-end workflow

```text
Excel BDH workbook  →  clean_bbg_export.py  →  bbg_treasury_panel.csv
                                                      ↓
                                            phase1_build.py
                                                      ↓
                                              phase1.json  →  Web UI (Vite)
```

**Typical session:**

1. Refresh data in Excel; save the workbook under `data/upload/` (see [Section 4](#4-step-a--bloomberg-excel-bdh-export)).
2. From the **repository root**: `python3 scripts/clean_bbg_export.py [yourfile.xlsx]`
3. `python3 scripts/phase1_build.py`
4. `cd web && npm install` (first time only), then `npm run dev` and open the printed URL.

---

## 4. Step A — Bloomberg Excel BDH export

### 4.1 Canonical paste layout

The project includes a **tab-separated template** showing how the BDH grid is arranged:

- File: [`references/BBG_US10Y_Backtest_BDH_Paste.tsv`](../references/BBG_US10Y_Backtest_BDH_Paste.tsv)

**Layout the cleaner expects** (first sheet):

| Row | Content |
| :--- | :--- |
| 0–1 | Start / end dates for BDH (e.g. `1/2/2000`, `=TODAY()`) — referenced as `$A$1`, `$A$2` in formulas |
| 2–3 | Headers: each series is a **3-column block** — Security, Field, empty spacer |
| 4+ | One `=BDH(...)` per series, spilling **Date** and **value** columns |

Use **one BDH per series**; paste from **A1** and refresh (**Shift+F9** or full calculation refresh) so values are live, not stale formulas.

### 4.2 Tickers and the 10Y anchor

- **`USGG10YR`** should appear as a column. The panel is **filtered to rows where USGG10YR is present**, so the backtest calendar matches generic Treasury 10Y dates and drops orphan dates from other calendars.
- Other columns (curves, inflation, vol, credit OAS, etc.) are merged on that calendar. Short-history series will have **NaN** on early dates; each factor’s backtest uses its **longest valid overlapping** window (see specs).

### 4.3 Saving the file

- Save as **`.xlsx`**.
- Default path expected by the cleaner (if you pass **no** argument) is:

  `data/upload/BBG_23Mar2026.xlsx`

- You may use any filename if you pass it explicitly to the script ([Section 5](#5-step-b--build-the-daily-panel-csv)).

---

## 5. Step B — Build the daily panel CSV

From the **repository root**:

```bash
python3 scripts/clean_bbg_export.py
```

Or with an explicit file:

```bash
python3 scripts/clean_bbg_export.py /path/to/your_export.xlsx
```

### Outputs

| Output | Description |
| :--- | :--- |
| `data/processed/bbg_treasury_panel.csv` | One row per date, columns = sanitized tickers |
| `data/processed/bbg_treasury_panel_meta.json` | Source path, row count, date range, column list, **missing %** per column |

**Column names:** Suffixes like ` Index`, ` Govt`, ` Curncy` are stripped for CSV headers (e.g. `USGG10YR Index` → `USGG10YR`).

If the input file is missing, the script exits with an error and prints the path it tried.

---

## 6. Step C — Build signals and `phase1.json`

```bash
python3 scripts/phase1_build.py
```

### What it does

- Reads `data/processed/bbg_treasury_panel.csv`.
- For each column, computes the Phase 1 signal and backtest (see [Section 9](#9-how-to-read-the-statistics)).
- Writes **`web/public/data/phase1.json`** (valid JSON: no raw `NaN` / `Infinity`).

### Optional: skip the causal sanity check

Each run, by default, runs a quick check that the signal at date `t` does not depend on **future values of the feature** after `t`. To skip (e.g. in automated jobs):

```bash
PHASE1_SKIP_CAUSAL_CHECK=1 python3 scripts/phase1_build.py
```

### Automated tests (developers)

```bash
python3 -m pytest tests/test_phase1_signal_timing.py -q
```

---

## 7. Step D — Run or publish the web dashboard

### Development (hot reload)

```bash
cd web
npm install    # first time
npm run dev
```

Open the URL Vite prints (often `http://localhost:5173/`; another port if that one is busy).

### Production static build

```bash
cd web
npm run build
```

Artifacts go to **`web/dist/`**. Serve that folder with any static file host. With `base: './'`, relative paths work if the app is not at the domain root.

The build includes **`phase1.json`** from `public/data/` as long as it exists before `npm run build`. **Rebuild** after regenerating JSON if you need the new data in `dist/`.

---

## 8. Using the dashboard

### 8.1 Header and methodology

- **Title** states that Phase 1 is **single-factor signals vs USGG10YR** (next-day yield change).
- **Signal specification** lists parameters from JSON (rolling window, thresholds, PnL definition, execution order, buy-and-hold definition). If something looks wrong, compare to [`specs/signals-backtest.md`](../specs/signals-backtest.md).

### 8.2 Main table

Rows are **one Bloomberg field / column** (human-readable **label**). Typical columns:

| Column | Meaning |
| :--- | :--- |
| **Ticker** | Factor name |
| **Signal** | Latest discrete view: **LONG DV01**, **SHORT DV01**, or **FLAT** |
| **Conf.** | Confidence `min(100, \|z\| × 28)` |
| **z** | Latest z-score of the feature’s daily change |
| **Sharpe** | Annualized Sharpe of the **strategy** daily PnL proxy over the factor’s valid sample |
| **B&H SR** | Sharpe of **constant long DV01** on the **same calendar rows** as that factor |
| **Hit** | Directional hit rate when the strategy is not flat (see spec) |
| **Cum Δy pts** | Sum of daily PnL proxy (yield points, not dollars) |
| **Max DD pts** | Worst drawdown of cumulative PnL proxy |
| **n** | Number of days in the sample |
| **History** | Start → end dates for that factor’s backtest |

Click a row to select it and open the **detail pane**.

### 8.3 Detail pane

- **Latest signal** recap: signal, confidence, z, **as of** date.
- **Cumulative PnL proxy (timeline):** chart with a **real date axis** (start / mid / end labels). **Solid** line = strategy; **dashed** = **buy-and-hold long DV01** on the same downsampled dates.
- **Cards:** strategy Sharpe with B&H Sharpe below; hit rate with B&H hit rate; cumulative Δy for strategy vs B&H.
- **Walk-forward Sharpe (8 folds):** eight **chronological** slices of the **same** rule (no refit); hover or note the date ranges on chips if your build shows titles.

### 8.4 Footer

Legal / methodology reminder: not advice; yield proxy; audit timing for production.

---

## 9. How to read the statistics

### 9.1 Signal construction (intuition)

- Take the **day-over-day change** in the feature.
- Compare that change to a **rolling** mean and volatility of past changes (**252** trading days, **126** minimum; statistics use only **past** changes via a one-day shift — causal).
- **z** = how extreme today’s change is vs that history.
- **Discrete signal:** `z > 0.5` → **+1** (positioned for **lower** yields vs the next move in USGG10YR), `z < -0.5` → **-1**, else **0**.

### 9.2 PnL proxy vs USGG10YR

For yield `y` = USGG10YR:

```text
daily PnL proxy = -signal_t × (y_{t+1} - y_t)
```

So **+1** is a **long duration** stance relative to the **next** daily yield change.

### 9.3 Buy-and-hold benchmark

**B&H** here means **always long DV01** on the **same days** as the factor’s backtest:

```text
daily B&H = -(y_{t+1} - y_t)
```

It answers: “How would a naive always-long-10y-move stance have done on **exactly** the days this factor was scored?”

### 9.4 Walk-forward chips

Eight equal-length **time** slices (chronological), each with its own Sharpe. This is **not** a rolling out-of-sample refit; it is a **stability** slice of the same fixed rule. See [`specs/signals-backtest.md`](../specs/signals-backtest.md) for limitations and future plans (IS/OOS, costs).

---

## 10. Execution timing and limitations

**What is guaranteed in code (feature side):**  
The signal at date `t` is built from the feature through `x_t` and rolling stats that **exclude** using `dx_t` in the mean/variance window (prior days only). The return leg uses **`y_{t+1} - y_t`**, so **`y_{t+1}`** is not an input to **`z_t`**.

**What is *not* solved here:**

- **Close-to-close** alignment across different Bloomberg fields may have **mixed economic settlement / publication** times. Treat live trading timing as a **separate audit** (see spec: execution-timing note).
- **No transaction costs**, **no DV01 hedging** to cash; **hit rate** and Sharpe are statistical summaries of a toy proxy.
- **Phase 1** is exploratory; composite signals, regime filters, and stricter OOS methodology are **future** work ([`TODO.md`](../TODO.md)).

---

## 11. Troubleshooting

| Symptom | What to check |
| :--- | :--- |
| Web shows “Could not load phase1.json” | Run `python3 scripts/phase1_build.py` from repo root; confirm `web/public/data/phase1.json` exists. Restart or refresh dev server. |
| `clean_bbg_export.py` says missing input | Path: default `data/upload/BBG_23Mar2026.xlsx` or pass `.xlsx` path as first argument. |
| Empty or very short panel | Ensure BDH spilled dates/values; **USGG10YR** present; save as `.xlsx` first sheet matching row layout ([Section 4](#4-step-a--bloomberg-excel-bdh-export)). |
| `phase1_build` exits early / few tickers | Panel may be missing columns or too short; each ticker needs enough valid days (see script threshold, typically hundreds of days). |
| B&H line missing in chart | Old JSON without `equity_buy_hold_cum`; regenerate with current `phase1_build.py`. |
| npm errors | Use a current Node LTS; delete `web/node_modules` and run `npm install` again. |
| Port already in use (`npm run dev`) | Vite picks another port; read the terminal URL. |

---

## 12. Where to go next

| Document | Audience |
| :--- | :--- |
| [`AGENTS.md`](../AGENTS.md) | Commands map, repo conventions |
| [`specs/data-pipeline.md`](../specs/data-pipeline.md) | Excel → CSV details |
| [`specs/signals-backtest.md`](../specs/signals-backtest.md) | Formal signal + JSON fields |
| [`specs/web-dashboard.md`](../specs/web-dashboard.md) | UI contract |
| [`.cursor/skills/chart-timeline/SKILL.md`](../.cursor/skills/chart-timeline/SKILL.md) | Convention for time-axis charts |

Questions about **Bloomberg BDH layout** in Excel: see the **bloomberg-excel-bdh** skill if you use Cursor skills, or align your sheet with `references/BBG_US10Y_Backtest_BDH_Paste.tsv`.
