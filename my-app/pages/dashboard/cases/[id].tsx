import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Link from "next/link";
import Sidebar from "../../../components/layout/Sidebar";
import { getCase, getSession, updateCaseOutcome, type CaseRecord } from "../../../lib/api";
import { ArrowLeft, CheckCircle2, ShieldAlert } from "lucide-react";

const outcomes = [
  { value: "CONFIRMED_SCAM", label: "Confirm scam" },
  { value: "LEGITIMATE", label: "Mark legitimate" },
  { value: "NEEDS_REVIEW", label: "Needs review" },
  { value: "ESCALATED", label: "Escalate" },
] as const;

export default function CaseDetail() {
  const router = useRouter();
  const caseId = typeof router.query.id === "string" ? router.query.id : "";
  const [item, setItem] = useState<CaseRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");
  useEffect(() => { if (!caseId) return; getCase(caseId).then((result) => { setItem(result); setNotes(result.notes ?? ""); }).catch((reason) => setError(reason instanceof Error ? reason.message : "Unable to load case.")).finally(() => setLoading(false)); }, [caseId]);

  async function recordOutcome(outcome: typeof outcomes[number]["value"]) {
    if (!item) return;
    setSaving(true); setError("");
    try {
      const user = await getSession();
      setItem(await updateCaseOutcome(item.case_id, { outcome, notes, analyst_id: user.email }));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to save case outcome."); }
    finally { setSaving(false); }
  }

  return <div className="app-shell"><Sidebar /><main className="main-content">
    <Link href="/dashboard/cases" className="back-link"><ArrowLeft size={15} /> Back to cases</Link>
    <header className="page-header"><div><div className="eyebrow">INVESTIGATIONS / CASE DETAIL</div><h1>{caseId || "Case"}</h1><p>Case facts and evidence loaded from the backend record.</p></div><span className="data-source-label">LIVE API DATA</span></header>
    {loading ? <section className="card empty-state">Loading case record…</section> : error && !item ? <section className="card empty-state error-copy" role="alert">Unable to load case: {error}</section> : item && <>
      <section className="metric-grid metric-grid-three"><article className="metric-card"><div className="metric-card-top"><span>Transaction</span></div><strong className="metric-id">{item.transaction_id}</strong></article><article className="metric-card"><div className="metric-card-top"><span>Risk score</span></div><strong>{item.decision?.risk_score ?? "Unavailable"}</strong><small>{item.decision?.risk_band ?? "No decision record"}</small></article><article className="metric-card"><div className="metric-card-top"><span>Recommended action</span></div><strong>{item.decision?.recommended_action ?? "Unavailable"}</strong><small>Case status: {item.status}</small></article></section>
      <section className="dashboard-grid case-content-grid"><article className="card"><div className="section-heading"><div><div className="eyebrow">DECISION EVIDENCE</div><h2>Signals and explanation</h2></div></div><p>{item.decision?.explanation ?? "No decision explanation is attached to this case."}</p>{item.signals.length ? <div className="evidence-list">{item.signals.map((signal, index) => <div className="evidence-row" key={`${signal.signal_type}-${index}`}><span className="risk-tag risk-elevated">{signal.signal_type}</span><strong>{signal.severity} pts</strong><p>{signal.evidence}</p><small>{signal.source_feature}: {signal.signal_value}</small></div>)}</div> : <p className="muted-copy">No persisted signal records.</p>}</article>
        <article className="card"><div className="eyebrow">INVESTIGATION</div><h2>Case status</h2><dl className="data-list"><div><dt>Status</dt><dd>{item.status}</dd></div><div><dt>Outcome</dt><dd>{item.outcome ?? "Pending"}</dd></div><div><dt>Assigned analyst</dt><dd>{item.analyst_id ?? "Unassigned"}</dd></div><div><dt>Created</dt><dd>{new Date(item.created_at).toLocaleString()}</dd></div><div><dt>Updated</dt><dd>{new Date(item.updated_at).toLocaleString()}</dd></div></dl></article></section>
      <section className="card case-action-card"><div className="eyebrow">ANALYST ACTION</div><h2>Record an outcome</h2><p className="muted-copy">Your decision and notes are persisted to the case and audit trail.</p><label htmlFor="case-notes">Investigation notes</label><textarea id="case-notes" value={notes} onChange={(event) => setNotes(event.target.value)} maxLength={2000} rows={4} />{error && <p className="form-error" role="alert">{error}</p>}<div className="outcome-actions">{outcomes.map(({ value, label }) => <button className="secondary-button" type="button" key={value} disabled={saving || item.status === "RESOLVED"} onClick={() => void recordOutcome(value)}>{saving ? "Saving…" : label}</button>)}</div>{item.status === "RESOLVED" && <p className="success-copy"><CheckCircle2 size={16} /> Outcome saved to the backend.</p>}</section>
      <section className="card"><div className="section-heading"><div><div className="eyebrow">AUDIT HISTORY</div><h2>Case timeline</h2></div><ShieldAlert size={18} /></div>{item.timeline.length ? <div className="compact-list">{item.timeline.map((event, index) => <div className="compact-row timeline-row" key={`${event.event}-${index}`}><span><strong>{event.event}</strong><small>{event.actor} · {new Date(event.created_at).toLocaleString()}</small></span></div>)}</div> : <div className="empty-state">No case-specific audit entries were returned.</div>}</section>
    </>}
  </main></div>;
}
