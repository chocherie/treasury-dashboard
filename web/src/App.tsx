import { useEffect, useId, useMemo, useState } from "react";

type StatsFull = {
  sharpe_ann: number | null;
  mean_daily: number | null;
  std_daily: number | null;
  cum_pnl_yield_pts: number | null;
  max_drawdown_pts: number | null;
  hit_rate: number | null;
  n: number;
};

type WFFold = {
  fold: number;
  start: string;
  end: string;
  sharpe: number | null;
  n: number;
};

type TickerRow = {
  id: string;
  label: string;
  history_start: string;
  history_end: string;
  n_days: number;
  last_date: string | null;
  last_signal: number;
  last_z: number | null;
  last_confidence: number;
  stats_full: StatsFull;
  buy_hold_same_period?: StatsFull;
  walk_forward: WFFold[];
  equity_dates: string[];
  equity_cum: number[];
  equity_buy_hold_cum?: number[];
};

type Phase1Payload = {
  generated_at: string;
  target: string;
  target_note: string;
  signal_spec: Record<string, string>;
  tickers: TickerRow[];
};

function signalLabel(s: number): string {
  if (s >= 1) return "LONG DV01";
  if (s <= -1) return "SHORT DV01";
  return "FLAT";
}

function signalClass(s: number): string {
  if (s >= 1) return "text-[var(--color-patina)]";
  if (s <= -1) return "text-[var(--color-ember)]";
  return "text-[var(--color-mist)]";
}

function fmtPct(x: number | null | undefined, d = 2): string {
  if (x === null || x === undefined || Number.isNaN(x)) return "—";
  return `${(100 * x).toFixed(d)}%`;
}

function fmtNum(x: number | null | undefined, d = 3): string {
  if (x === null || x === undefined || Number.isNaN(x)) return "—";
  return x.toFixed(d);
}

function parseChartTime(isoDate: string): number {
  const s = isoDate.includes("T") ? isoDate : `${isoDate}T12:00:00Z`;
  return Date.parse(s);
}

function fmtAxisDate(isoDate: string): string {
  const [y, m] = isoDate.split("-");
  if (!y || !m) return isoDate;
  const mo = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][Number(m) - 1] ?? m;
  return `${mo} '${y.slice(2)}`;
}

/** Cumulative series with a real date axis (start / mid / end) and optional buy & hold overlay. */
function EquityTimelineChart({
  dates,
  strategy,
  buyHold,
  gradStratId,
  gradBhId,
}: {
  dates: string[];
  strategy: number[];
  buyHold: number[] | null;
  gradStratId: string;
  gradBhId: string;
}) {
  const w = 340;
  const chartH = 52;
  const axisH = 18;
  const padX = 6;
  const padY = 5;
  const totalH = chartH + axisH;

  if (dates.length < 2 || strategy.length < 2 || dates.length !== strategy.length) {
    return <div className="h-[70px] w-full max-w-[340px] rounded bg-white/5" />;
  }

  const t0 = parseChartTime(dates[0]);
  const t1 = parseChartTime(dates[dates.length - 1]);
  const spanT = t1 - t0 || 1;

  const seriesForRange = buyHold && buyHold.length === strategy.length ? [...strategy, ...buyHold] : [...strategy];
  const minV = Math.min(...seriesForRange);
  const maxV = Math.max(...seriesForRange);
  const spanV = maxV - minV || 1;

  const xAt = (i: number) => {
    const ti = parseChartTime(dates[i]);
    return padX + ((ti - t0) / spanT) * (w - 2 * padX);
  };
  const yAt = (v: number) => padY + (1 - (v - minV) / spanV) * (chartH - 2 * padY);

  const linePath = (vals: number[]) => {
    const pts = vals.map((v, i) => `${xAt(i)},${yAt(v)}`);
    return `M ${pts.join(" L ")}`;
  };

  const mid = Math.floor((dates.length - 1) / 2);
  const ticks = [
    { i: 0, label: fmtAxisDate(dates[0]) },
    { i: mid, label: fmtAxisDate(dates[mid]) },
    { i: dates.length - 1, label: fmtAxisDate(dates[dates.length - 1]) },
  ];

  return (
    <div className="w-full max-w-[340px]">
      <svg
        width="100%"
        viewBox={`0 0 ${w} ${totalH}`}
        className="overflow-visible text-[9px] fill-white/45"
        role="img"
        aria-label="Cumulative PnL proxy vs time; strategy and buy-and-hold long DV01"
      >
        <defs>
          <linearGradient id={gradStratId} x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="var(--color-copper)" stopOpacity="0.25" />
            <stop offset="100%" stopColor="var(--color-copper)" stopOpacity="0.95" />
          </linearGradient>
          <linearGradient id={gradBhId} x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="var(--color-mist)" stopOpacity="0.2" />
            <stop offset="100%" stopColor="var(--color-mist)" stopOpacity="0.75" />
          </linearGradient>
        </defs>
        <line
          x1={padX}
          x2={w - padX}
          y1={chartH}
          y2={chartH}
          stroke="white"
          strokeOpacity={0.12}
          strokeWidth={1}
        />
        {buyHold && buyHold.length === strategy.length ? (
          <path
            d={linePath(buyHold)}
            fill="none"
            stroke={`url(#${gradBhId})`}
            strokeWidth={1.25}
            strokeDasharray="4 3"
            vectorEffect="non-scaling-stroke"
          />
        ) : null}
        <path
          d={linePath(strategy)}
          fill="none"
          stroke={`url(#${gradStratId})`}
          strokeWidth={1.6}
          vectorEffect="non-scaling-stroke"
        />
        {ticks.map((tk) => (
          <text key={tk.i} x={xAt(tk.i)} y={totalH - 3} textAnchor="middle" className="font-mono">
            {tk.label}
          </text>
        ))}
      </svg>
      <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-[10px] text-white/45">
        <span>
          <span className="text-[var(--color-copper)]">━━</span> Strategy
        </span>
        {buyHold && buyHold.length === strategy.length ? (
          <span>
            <span className="text-[var(--color-mist)]">┅┅</span> Buy &amp; hold (long DV01)
          </span>
        ) : null}
      </div>
    </div>
  );
}

export default function App() {
  const chartUid = useId().replace(/:/g, "");
  const gradStratId = `lg-strat-${chartUid}`;
  const gradBhId = `lg-bh-${chartUid}`;

  const [data, setData] = useState<Phase1Payload | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [sel, setSel] = useState<TickerRow | null>(null);

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/phase1.json`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setData)
      .catch((e) => setErr(String(e)));
  }, []);

  const specLines = useMemo(() => {
    if (!data) return [];
    return Object.entries(data.signal_spec);
  }, [data]);

  if (err) {
    return (
      <div className="min-h-screen flex items-center justify-center p-8 text-[var(--color-ember)]">
        Could not load phase1.json — run <code className="mx-1 text-[var(--color-paper)]">python3 scripts/phase1_build.py</code>{" "}
        then <code className="mx-1">npm run dev</code> in <code className="mx-1">web/</code>. ({err})
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center text-[var(--color-mist)] tracking-widest text-xs uppercase">
        Loading panel…
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--color-ink)] relative">
      <div
        className="pointer-events-none fixed inset-0 opacity-[0.07]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
        }}
      />

      <header className="relative border-b border-white/10 px-6 py-10 md:px-12">
        <p className="text-[10px] uppercase tracking-[0.35em] text-[var(--color-copper)] mb-3">Treasury dashboard</p>
        <h1
          className="font-[family-name:var(--font-display)] text-4xl md:text-5xl text-[var(--color-paper)] leading-tight max-w-3xl"
          style={{ fontFamily: "var(--font-display)" }}
        >
          Phase 1 · single-factor signals vs <span className="text-[var(--color-copper)]">{data.target}</span>
        </h1>
        <p className="mt-4 max-w-2xl text-[var(--color-mist)] text-sm leading-relaxed">{data.target_note}</p>
        <p className="mt-3 text-[11px] text-white/35">
          Generated {new Date(data.generated_at).toLocaleString()} · Each row is one Bloomberg field, longest overlapping
          history.
        </p>
      </header>

      <section className="relative px-6 md:px-12 py-8 border-b border-white/10">
        <h2 className="text-xs uppercase tracking-[0.2em] text-[var(--color-mist)] mb-4">Signal specification</h2>
        <ul className="grid md:grid-cols-2 gap-x-12 gap-y-2 text-xs text-white/70 max-w-4xl">
          {specLines.map(([k, v]) => (
            <li key={k} className="flex gap-2">
              <span className="text-[var(--color-copper)] shrink-0 w-40">{k}</span>
              <span>{v}</span>
            </li>
          ))}
        </ul>
      </section>

      <main className="relative grid lg:grid-cols-[1fr_380px] gap-0 min-h-[60vh]">
        <div className="overflow-x-auto border-b lg:border-b-0 lg:border-r border-white/10">
          <table className="w-full text-left text-xs min-w-[980px]">
            <thead>
              <tr className="text-[var(--color-mist)] uppercase tracking-wider border-b border-white/10">
                <th className="py-3 px-4 font-medium">Ticker</th>
                <th className="py-3 px-2 font-medium">Signal</th>
                <th className="py-3 px-2 font-medium">Conf.</th>
                <th className="py-3 px-2 font-medium">z</th>
                <th className="py-3 px-2 font-medium">Sharpe</th>
                <th className="py-3 px-2 font-medium" title="Buy &amp; hold long DV01, same dates">
                  B&amp;H SR
                </th>
                <th className="py-3 px-2 font-medium">Hit</th>
                <th className="py-3 px-2 font-medium">Cum Δy pts</th>
                <th className="py-3 px-2 font-medium">Max DD pts</th>
                <th className="py-3 px-2 font-medium">n</th>
                <th className="py-3 px-4 font-medium">History</th>
              </tr>
            </thead>
            <tbody>
              {data.tickers.map((t) => (
                <tr
                  key={t.id}
                  onClick={() => setSel(t)}
                  className={`cursor-pointer border-b border-white/[0.06] hover:bg-white/[0.04] transition-colors ${
                    sel?.id === t.id ? "bg-white/[0.06]" : ""
                  }`}
                >
                  <td className="py-3 px-4 font-medium text-[var(--color-paper)]">{t.label}</td>
                  <td className={`py-3 px-2 font-semibold ${signalClass(t.last_signal)}`}>{signalLabel(t.last_signal)}</td>
                  <td className="py-3 px-2 text-[var(--color-paper)]">{fmtNum(t.last_confidence, 1)}</td>
                  <td className="py-3 px-2 text-white/60">{fmtNum(t.last_z, 2)}</td>
                  <td className="py-3 px-2 text-[var(--color-copper)]">{fmtNum(t.stats_full.sharpe_ann, 2)}</td>
                  <td className="py-3 px-2 text-white/50">{fmtNum(t.buy_hold_same_period?.sharpe_ann, 2)}</td>
                  <td className="py-3 px-2 text-white/60">{fmtPct(t.stats_full.hit_rate)}</td>
                  <td className="py-3 px-2 text-white/60">{fmtNum(t.stats_full.cum_pnl_yield_pts, 2)}</td>
                  <td className="py-3 px-2 text-[var(--color-ember)]">{fmtNum(t.stats_full.max_drawdown_pts, 2)}</td>
                  <td className="py-3 px-2 text-white/50">{t.stats_full.n}</td>
                  <td className="py-3 px-4 text-white/40 whitespace-nowrap">
                    {t.history_start} → {t.history_end}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <aside className="p-6 lg:p-8 bg-[var(--color-depth)]/80 backdrop-blur-sm">
          {sel ? (
            <div className="space-y-6">
              <div>
                <p className="text-[10px] uppercase tracking-[0.25em] text-[var(--color-mist)]">Selected</p>
                <h3 className="font-[family-name:var(--font-display)] text-2xl text-[var(--color-paper)] mt-1" style={{ fontFamily: "var(--font-display)" }}>
                  {sel.label}
                </h3>
                <p className={`text-sm mt-2 font-semibold ${signalClass(sel.last_signal)}`}>{signalLabel(sel.last_signal)}</p>
                <p className="text-xs text-white/50 mt-1">
                  Confidence {fmtNum(sel.last_confidence, 1)} · z {fmtNum(sel.last_z, 3)} · as of {sel.last_date}
                </p>
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-[0.2em] text-[var(--color-mist)] mb-2">
                  Cumulative PnL proxy (timeline)
                </p>
                <EquityTimelineChart
                  dates={sel.equity_dates}
                  strategy={sel.equity_cum}
                  buyHold={
                    sel.equity_buy_hold_cum && sel.equity_buy_hold_cum.length === sel.equity_cum.length
                      ? sel.equity_buy_hold_cum
                      : null
                  }
                  gradStratId={gradStratId}
                  gradBhId={gradBhId}
                />
              </div>
              <div className="grid grid-cols-2 gap-3 text-[11px]">
                <div className="rounded border border-white/10 p-3">
                  <p className="text-[var(--color-mist)]">Ann. Sharpe</p>
                  <p className="text-lg text-[var(--color-copper)] mt-1">{fmtNum(sel.stats_full.sharpe_ann, 2)}</p>
                  <p className="text-[10px] text-white/35 mt-1">
                    B&amp;H {fmtNum(sel.buy_hold_same_period?.sharpe_ann, 2)}
                  </p>
                </div>
                <div className="rounded border border-white/10 p-3">
                  <p className="text-[var(--color-mist)]">Hit rate</p>
                  <p className="text-lg text-[var(--color-paper)] mt-1">{fmtPct(sel.stats_full.hit_rate)}</p>
                  <p className="text-[10px] text-white/35 mt-1">B&amp;H {fmtPct(sel.buy_hold_same_period?.hit_rate)}</p>
                </div>
                <div className="rounded border border-white/10 p-3 col-span-2">
                  <p className="text-[var(--color-mist)]">Cum Δy pts (full sample)</p>
                  <p className="text-sm text-white/80 mt-1">
                    Strategy <span className="text-[var(--color-copper)]">{fmtNum(sel.stats_full.cum_pnl_yield_pts, 2)}</span>
                    <span className="text-white/30 mx-2">·</span>
                    B&amp;H{" "}
                    <span className="text-[var(--color-mist)]">{fmtNum(sel.buy_hold_same_period?.cum_pnl_yield_pts, 2)}</span>
                  </p>
                </div>
                <div className="rounded border border-white/10 p-3 col-span-2">
                  <p className="text-[var(--color-mist)]">Walk-forward Sharpe (8 folds)</p>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {sel.walk_forward.map((w) => (
                      <span
                        key={w.fold}
                        className="px-2 py-1 rounded bg-white/5 text-[10px] text-white/70"
                        title={`${w.start}–${w.end}`}
                      >
                        F{w.fold}: {fmtNum(w.sharpe, 2)}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-sm text-[var(--color-mist)] leading-relaxed">
              Select a ticker row to inspect cumulative backtest, walk-forward Sharpe slices, and latest signal strength.
            </p>
          )}
        </aside>
      </main>

      <footer className="relative px-6 md:px-12 py-10 text-[10px] text-white/30 uppercase tracking-wider border-t border-white/10">
        Not investment advice · PnL is a yield-change proxy, not traded cash · Audit execution timing for production use
      </footer>
    </div>
  );
}
