# Treasury dashboard

**User guide (step-by-step):** [`docs/user-guide.md`](docs/user-guide.md)

Agent onboarding: read [`AGENTS.md`](AGENTS.md) (map + learned prefs), then [`docs/architecture.md`](docs/architecture.md) and [`specs/README.md`](specs/README.md).

## Phase 1

1. **Bloomberg export** — Paste the BDH grid from `references/BBG_US10Y_Backtest_BDH_Paste.tsv` into Excel, refresh, save as `data/upload/BBG_23Mar2026.xlsx` (or any name).
2. **Clean panel** — `python3 scripts/clean_bbg_export.py` → `data/processed/bbg_treasury_panel.csv`
3. **Signals + backtest JSON** — `python3 scripts/phase1_build.py` → `web/public/data/phase1.json`
4. **Web app** — `cd web && npm install && npm run dev` then open the URL shown (Vite).

Static build: `cd web && npm run build`; serve `web/dist/` with any static host. `phase1.json` is copied into `dist/data/` on build.

### Publishing to GitHub

From the repo root (after `git` is initialized and you have a commit):

1. Create a **new empty repository** on GitHub (no README/license if you already have them locally).
2. Add the remote and push:

```bash
git remote add origin https://github.com/chocherie/treasury-dashboard.git
git branch -M main
git push -u origin main
```

Bloomberg **Excel** exports under `data/upload/` stay **ignored** by git (see `.gitignore`); commit the **processed CSV** / **phase1.json** or regenerate after clone per `docs/user-guide.md`.

### Deploy on Vercel

The repo includes [`vercel.json`](vercel.json) (install/build in `web/`, output `web/dist`). Connect [chocherie/treasury-dashboard](https://github.com/chocherie/treasury-dashboard) in the Vercel dashboard or run `npx vercel@latest deploy --prod` from the repo root.

**Production URL:** [https://treasury-dashboard-pi.vercel.app](https://treasury-dashboard-pi.vercel.app)

### Python deps

```bash
pip install pandas numpy openpyxl
```

### Methodology (Phase 1)

Per ticker: rolling z-score of **daily changes** (252d window, 126d min), discrete **±1 / 0** vs threshold 0.5, **confidence** = min(100, |z|×28). PnL proxy vs **USGG10YR**: `-signal × Δy` for the next close-to-close move. Walk-forward table = eight chronological Sharpe slices (same rule, no refit).
