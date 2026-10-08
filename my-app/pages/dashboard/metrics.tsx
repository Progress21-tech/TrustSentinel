import { useEffect, useState } from "react";
import Sidebar from "../../components/layout/Sidebar";
import { getMetrics } from "../../lib/api";
import { Activity, AlertTriangle, Clock3, ShieldCheck } from "lucide-react";

export default function Metrics() {
  const [metrics, setMetrics] = useState<Awaited<ReturnType<typeof getMetrics>> | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => { getMetrics().then(setMetrics).catch((reason) => setError(reason instanceof Error ? reason.message : "Metrics are unavailable.")).finally(() => setLoading(false)); }, []);
  const records = [
    { name: "Evaluated transactions", value: metrics?.transactions_evaluated, icon: Activity },
    { name: "Elevated and above", value: metrics?.high_risk_transactions, icon: AlertTriangle },
    { name: "Warnings and step-ups", value: metrics ? metrics.warnings + metrics.step_ups : undefined, icon: ShieldCheck },
    { name: "Average decision latency", value: metrics ? `${metrics.average_latency_ms} ms` : undefined, icon: Clock3 },
  ];
  const actions = metrics ? [{ name: "WARN", count: metrics.warnings }, { name: "STEP_UP", count: metrics.step_ups }, { name: "HOLD", count: metrics.holds }, { name: "REVIEW", count: metrics.reviews }] : [];
  return <div className="app-shell"><Sidebar /><main className="main-content">
    <header className="page-header"><div><div className="eyebrow">RISK OPERATIONS / ANALYTICS</div><h1>Metrics</h1><p>Aggregate counters reported by the TrustSentinel backend.</p></div><span className="data-source-label">BACKEND DATA</span></header>
    {error && <div className="notice notice-error" role="alert">Metrics could not be loaded: {error}</div>}
    <section className="metric-grid">{records.map(({ name, value, icon: Icon }) => <article className="metric-card" key={name}><div className="metric-card-top"><span>{name}</span><Icon size={17} /></div><strong>{loading ? "—" : value === undefined ? "Unavailable" : typeof value === "number" ? value.toLocaleString() : value}</strong><small>Persisted backend aggregate</small></article>)}</section>
    <section className="dashboard-grid analytics-grid"><article className="card"><div className="eyebrow">ACTION COUNTS</div><h2>Intervention totals</h2><p className="muted-copy">Action counts from saved backend interventions.</p>{loading ? <div className="empty-state">Loading metrics…</div> : !metrics ? <div className="empty-state">No metrics are available.</div> : actions.map((item) => <div className="distribution-row" key={item.name}><span>{item.name}</span><strong>{item.count.toLocaleString()}</strong></div>)}</article>
      <article className="card"><div className="eyebrow">CASE ACTIVITY</div><h2>Investigation summary</h2>{loading ? <div className="empty-state">Loading metrics…</div> : metrics ? <dl className="data-list"><div><dt>Cases created</dt><dd>{metrics.cases_created.toLocaleString()}</dd></div><div><dt>Analyst actions</dt><dd>{metrics.analyst_actions.toLocaleString()}</dd></div><div><dt>High-risk transaction rate</dt><dd>{(metrics.high_risk_rate * 100).toFixed(1)}%</dd></div><div><dt>Interventions recorded</dt><dd>{(metrics.warnings + metrics.step_ups + metrics.holds + metrics.reviews).toLocaleString()}</dd></div></dl> : <div className="empty-state">Case metrics unavailable.</div>}</article></section>
    <p className="source-note">Metrics are aggregate records from the configured backend database. Any sandbox-generated records are synthetic and should not be interpreted as real-world fraud performance.</p>
  </main></div>;
}
