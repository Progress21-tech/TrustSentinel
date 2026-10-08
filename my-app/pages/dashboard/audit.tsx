import { useEffect, useState } from "react";
import Sidebar from "../../components/layout/Sidebar";
import { getAuditEvents } from "../../lib/api";
import { FileClock, FileText } from "lucide-react";

export default function AuditLog() {
  const [data, setData] = useState<Awaited<ReturnType<typeof getAuditEvents>> | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => { getAuditEvents().then(setData).catch((reason) => setError(reason instanceof Error ? reason.message : "Audit events are unavailable.")).finally(() => setLoading(false)); }, []);
  return <div className="app-shell"><Sidebar /><main className="main-content">
    <header className="page-header"><div><div className="eyebrow">GOVERNANCE / TRACEABILITY</div><h1>Audit trail</h1><p>Events recorded by the backend risk and case workflows.</p></div><span className="data-source-label">BACKEND DATA</span></header>
    <section className="metric-grid metric-grid-three"><article className="metric-card"><div className="metric-card-top"><span>Events returned</span><FileClock size={17} /></div><strong>{loading ? "—" : data?.count.toLocaleString() ?? "Unavailable"}</strong><small>Latest 100 records</small></article><article className="metric-card"><div className="metric-card-top"><span>Risk decisions</span><FileText size={17} /></div><strong>{loading ? "—" : data?.items.filter((event) => event.event === "RISK_DECISION_CREATED").length.toLocaleString() ?? "Unavailable"}</strong><small>Within the loaded event window</small></article><article className="metric-card"><div className="metric-card-top"><span>Case events</span><FileClock size={17} /></div><strong>{loading ? "—" : data?.items.filter((event) => event.entity_type === "case").length.toLocaleString() ?? "Unavailable"}</strong><small>Within the loaded event window</small></article></section>
    <section className="card"><div className="section-heading"><div><h2>Recent audit events</h2><p>Newest records returned by `/v1/audit`.</p></div></div>
      {loading ? <div className="empty-state">Loading audit history…</div> : error ? <div className="empty-state error-copy" role="alert">Unable to load audit history: {error}</div> : !data?.items.length ? <div className="empty-state">No audit events recorded yet.</div> : <div className="audit-list">{data.items.map((event, index) => <article className="audit-row" key={`${event.entity_id}-${event.event}-${index}`}><div className="audit-icon"><FileText size={16} /></div><div className="audit-event"><div className="audit-event-top"><strong>{event.event}</strong><span className="case-status">{event.entity_type}</span></div><div className="audit-meta"><span>{event.actor}</span><span>{event.entity_id}</span><time>{new Date(event.created_at).toLocaleString()}</time></div><pre className="audit-metadata">{JSON.stringify(event.metadata, null, 2)}</pre></div></article>)}</div>}
    </section>
  </main></div>;
}
