import { useEffect, useState } from "react";
import Link from "next/link";
import Sidebar from "../../components/layout/Sidebar";
import { getCases, getMetrics, getTransactions } from "../../lib/api";
import { Activity, ArrowUpRight, BriefcaseBusiness, Clock3, ShieldAlert, Waypoints } from "lucide-react";

type DashboardData = {
  metrics: Awaited<ReturnType<typeof getMetrics>> | null;
  transactions: Awaited<ReturnType<typeof getTransactions>>["items"] | null;
  cases: Awaited<ReturnType<typeof getCases>>["items"] | null;
  errors: string[];
};

const empty: DashboardData = { metrics: null, transactions: null, cases: null, errors: [] };

export default function Dashboard() {
  const [data, setData] = useState(empty);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let active = true;
    Promise.allSettled([getMetrics(), getTransactions(8), getCases({ status: "OPEN" })] as const).then((results) => {
      if (!active) return;
      const errors: string[] = [];
      const metrics = results[0].status === "fulfilled" ? results[0].value : null;
      const transactions = results[1].status === "fulfilled" ? results[1].value.items : null;
      const cases = results[2].status === "fulfilled" ? results[2].value.items : null;
      results.forEach((result) => { if (result.status === "rejected") errors.push(result.reason instanceof Error ? result.reason.message : "A dashboard data request failed."); });
      setData({ metrics, transactions, cases, errors });
      setLoading(false);
    });
    return () => { active = false; };
  }, []);

  const metrics = data.metrics;
  const values = [
    { label: "Evaluated transactions", value: metrics?.transactions_evaluated, icon: Waypoints, note: "Persisted risk decisions" },
    { label: "Elevated and above", value: metrics?.high_risk_transactions, icon: ShieldAlert, note: "Backend risk classification" },
    { label: "Open investigations", value: data.cases?.length, icon: BriefcaseBusiness, note: data.cases ? "Current open case queue" : "Case data unavailable" },
    { label: "Mean decision latency", value: metrics ? `${metrics.average_latency_ms} ms` : undefined, icon: Clock3, note: "Recorded by the risk engine" },
  ];

  return <div className="app-shell"><Sidebar /><main className="main-content">
    <header className="page-header"><div><div className="eyebrow">RISK OPERATIONS / OVERVIEW</div><h1>Decision overview</h1><p>Signals and persisted decisions from TrustSentinel.</p></div><span className="data-source-label">BACKEND DATA</span></header>
    {data.errors.length > 0 && <div className="notice notice-error" role="status"><strong>Some live data could not be loaded.</strong><span>{data.errors.join(" · ")}</span></div>}
    <section className="metric-grid">
      {values.map(({ label, value, icon: Icon, note }) => <article className="metric-card" key={label}><div className="metric-card-top"><span>{label}</span><Icon size={17} /></div><strong>{loading ? "—" : value === undefined ? "Unavailable" : typeof value === "number" ? value.toLocaleString() : value}</strong><small>{note}</small></article>)}
    </section>
    <section className="dashboard-grid dashboard-main-grid">
      <article className="card table-card"><div className="section-heading"><div><div className="eyebrow">LATEST RECORDS</div><h2>Recent decisions</h2><p>Most recent persisted transactions returned by the API.</p></div><Link href="/dashboard/transactions" className="subtle-link">All transactions <ArrowUpRight size={15} /></Link></div>
        {loading ? <div className="empty-state">Loading transaction records…</div> : data.transactions === null ? <div className="empty-state">Transaction data is unavailable.</div> : data.transactions.length === 0 ? <div className="empty-state">No transaction decisions recorded yet.</div> : <div className="table-wrap"><table><thead><tr><th>Transaction</th><th>Account</th><th>Amount</th><th>Risk</th><th>Action</th></tr></thead><tbody>{data.transactions.map((item) => {
          const decision = item.risk_decision as { risk_score: number; risk_band: string; recommended_action: string } | null;
          return <tr key={String(item.transaction_id)}><td><Link className="table-link" href={`/dashboard/transactions/${encodeURIComponent(String(item.transaction_id))}`}>{String(item.transaction_id)}</Link></td><td>{String(item.account_id)}</td><td>{item.amount == null ? "—" : `${String(item.currency)} ${Number(item.amount).toLocaleString()}`}</td><td>{decision ? <><span className={`risk-dot risk-${decision.risk_band.toLowerCase()}`} />{decision.risk_band} · {decision.risk_score}</> : "No decision"}</td><td>{decision?.recommended_action ?? "—"}</td></tr>;
        })}</tbody></table></div>}
      </article>
      <article className="card queue-card"><div className="section-heading"><div><div className="eyebrow">INVESTIGATIONS</div><h2>Open cases</h2><p>Current cases from the backend.</p></div><BriefcaseBusiness size={18} /></div>
        {loading ? <div className="empty-state">Loading cases…</div> : data.cases === null ? <div className="empty-state">Case data is unavailable.</div> : data.cases.length === 0 ? <div className="empty-state">No open risk cases.</div> : <div className="compact-list">{data.cases.slice(0, 6).map((item) => <Link href={`/dashboard/cases/${encodeURIComponent(item.case_id)}`} className="compact-row" key={item.case_id}><span><strong>{item.case_id}</strong><small>{item.transaction_id}</small></span><span className="case-status">{item.status}</span></Link>)}</div>}
      </article>
    </section>
    <section className="source-note"><Activity size={15} /> Dashboard values are read from persisted backend metrics, transactions, and cases. Synthetic sandbox activity is identified when run.</section>
  </main></div>;
}
