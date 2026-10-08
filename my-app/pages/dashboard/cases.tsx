import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import Sidebar from "../../components/layout/Sidebar";
import { getCases, type CaseRecord } from "../../lib/api";
import { Search } from "lucide-react";

export default function Cases() {
  const [items, setItems] = useState<CaseRecord[] | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("ALL");
  useEffect(() => { getCases().then((result) => setItems(result.items)).catch((reason) => setError(reason instanceof Error ? reason.message : "Unable to load cases.")).finally(() => setLoading(false)); }, []);
  const filtered = useMemo(() => (items ?? []).filter((item) => (status === "ALL" || item.status === status) && `${item.case_id} ${item.transaction_id}`.toLowerCase().includes(search.toLowerCase())), [items, status, search]);

  return <div className="app-shell"><Sidebar /><main className="main-content">
    <header className="page-header"><div><div className="eyebrow">INVESTIGATIONS / CASE QUEUE</div><h1>Cases</h1><p>Review cases persisted by the TrustSentinel risk service.</p></div><span className="data-source-label">BACKEND DATA</span></header>
    <section className="card filter-bar"><label className="search-box"><Search size={16} /><span className="sr-only">Search case or transaction</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search case or transaction" /></label><label className="filter-select"><span className="sr-only">Filter case status</span><select value={status} onChange={(event) => setStatus(event.target.value)}><option value="ALL">All statuses</option><option value="OPEN">Open</option><option value="IN_REVIEW">In review</option><option value="ESCALATED">Escalated</option><option value="RESOLVED">Resolved</option></select></label></section>
    <section className="card table-card"><div className="section-heading"><div><h2>Investigation queue</h2><p>{items?.length ?? 0} cases returned by the backend</p></div></div>
      {loading ? <div className="empty-state">Loading cases…</div> : error ? <div className="empty-state error-copy" role="alert">Unable to load cases: {error}</div> : filtered.length === 0 ? <div className="empty-state">{items?.length ? "No cases match your search." : "No risk cases recorded yet."}</div> : <div className="table-wrap"><table><thead><tr><th>Case</th><th>Transaction</th><th>Score / band</th><th>Action</th><th>Status</th><th>Outcome</th><th>Created</th></tr></thead><tbody>{filtered.map((item) => <tr key={item.case_id}><td><Link className="table-link" href={`/dashboard/cases/${encodeURIComponent(item.case_id)}`}>{item.case_id}</Link></td><td>{item.transaction_id}</td><td>{item.decision ? <><strong>{item.decision.risk_score}</strong> <span className={`risk-tag risk-${item.decision.risk_band.toLowerCase()}`}>{item.decision.risk_band}</span></> : "—"}</td><td>{item.decision?.recommended_action ?? "—"}</td><td><span className="case-status">{item.status}</span></td><td>{item.outcome ?? "Awaiting review"}</td><td>{new Date(item.created_at).toLocaleString()}</td></tr>)}</tbody></table></div>}
    </section>
  </main></div>;
}
