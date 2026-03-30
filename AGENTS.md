# Treasury dashboard

Bloomberg-driven US Treasury research stack: clean BDH exports to a daily panel, per-factor signals vs **USGG10YR**, Phase 1 web dashboard.

## Non-Negotiable Rules

1. **Read the spec before coding.** Before editing `scripts/` or `web/src/`, read the matching file in `specs/` (see `specs/README.md`).
2. **Update docs after every change.** Touch `TODO.md`, `docs/quality.md`, and `specs/README.md` / the relevant spec when behavior changes.
3. **Write artifacts to disk.** Plans, reports, and spec updates live in the repo — not only in chat.
4. **Specs and code must agree.** Reconcile immediately if they diverge.

## Repository Map

| Document | Purpose |
| :--- | :--- |
| `docs/user-guide.md` | End-to-end workflow for Bloomberg → panel → JSON → web UI |
| `docs/architecture.md` | System map, directories, tech stack |
| `docs/core-beliefs.md` | Agent operating principles |
| `docs/quality.md` | Domain grades and gaps |
| `specs/README.md` | Spec index + verification |
| `specs/testing-strategy.md` | Target testing approach |
| `TODO.md` | Phased tasks |
| `docs/plans/active/` | ExecPlans for multi-system work |
| `.cursor/skills/chart-timeline/` | Time-series charts must show dates + axis labels (see `SKILL.md`) |
| `.agents/workflows/` | implement-and-verify, safe-refactor, verify-ui-properties |

### Cursor rules

| Rule | Enforces |
| :--- | :--- |
| `.cursor/rules/update-docs-after-changes.mdc` | Doc updates after implementation |
| `.cursor/rules/read-spec-before-coding.mdc` | Spec-first for `web/src/**`, `scripts/**` |
| `.cursor/rules/artifacts-to-disk.mdc` | Plans/reports on disk |

## Commands

| Command | Purpose |
| :--- | :--- |
| `pip install pandas numpy openpyxl` | Python deps |
| `python3 scripts/clean_bbg_export.py` | Excel → `data/processed/bbg_treasury_panel.csv` |
| `python3 scripts/phase1_build.py` | Panel → `web/public/data/phase1.json` |
| `cd web && npm install && npm run dev` | Dashboard dev server |
| `cd web && npm run build` | Production static build → `web/dist/` |
| `bombadil test http://localhost:5173 --headless` | UI properties (when Bombadil installed) |

## How to Work in This Repo

1. Read `TODO.md` for the current phase.
2. Open the spec for the system you change (`specs/data-pipeline.md`, `signals-backtest.md`, or `web-dashboard.md`).
3. Implement; add tests per `specs/testing-strategy.md` when extending logic.
4. For web UI changes, follow `.agents/workflows/verify-ui-properties.md` when Bombadil is available.
5. After substantive work, run `.agents/workflows/implement-and-verify.md`.
6. Update `docs/quality.md` and spec verification rows.

## Environment Variables

None required for Phase 1 (Bloomberg runs on the user’s machine).

---

## Learned User Preferences

- Prefer Bloomberg and Excel BDH (paste grid, Shift+F9) for historical series in this Treasury dashboard project.
- When designing holding rules, allow daily signal refresh but keep execution turnover low (e.g. weekly rebalance, minimum hold days, or signal persistence before flipping).
- Prefer the longest overlapping backtest window per feature, accepting different start dates when a series has shorter history.

## Learned Workspace Facts

- Canonical BDH paste layout lives at `references/BBG_US10Y_Backtest_BDH_Paste.tsv` (tab-separated three-column blocks per series).
- Bloomberg Excel exports are saved under `data/upload/`; `scripts/clean_bbg_export.py` builds `data/processed/bbg_treasury_panel.csv` on a single date index aligned to days where `USGG10YR` exists.
- HY/IG credit inputs in the panel are `USOHHYTO` and `USOAIGTO` (Bloomberg USD All Sectors OAS); usable daily history begins around 2012.
- Phase 1 pipeline: `scripts/phase1_build.py` outputs `web/public/data/phase1.json`; the web UI is under `web/` (Vite + React).
