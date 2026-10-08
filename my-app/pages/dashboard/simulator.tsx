import { useState } from "react";
import Sidebar from "../../components/layout/Sidebar";
import { getAuditEvents, getTransaction, runScenario, type RiskResult } from "../../lib/api";
import { CheckCircle2, CircleAlert, Loader2, Play, ShieldAlert } from "lucide-react";

const scenarios = [
  { id: "normal", title: "Normal", description: "Established payment context." },
  { id: "legitimate_high_value", title: "Legitimate high value", description: "High value with established context." },
  { id: "new_beneficiary_large_amount", title: "New beneficiary · large amount", description: "New recipient and unusual amount." },
  { id: "new_device_large_transfer", title: "New device · large transfer", description: "Unfamiliar device and transfer." },
  { id: "rapid_transfers", title: "Rapid transfers", description: "Elevated recent transaction velocity." },
  { id: "risky_beneficiary", title: "Risky beneficiary", description: "Beneficiary has synthetic risk history." },
  { id: "account_recovery_new_beneficiary", title: "Account recovery", description: "Recovery followed by new beneficiary activity." },
  { id: "combined_high_risk", title: "Combined indicators", description: "Multiple contextual risk indicators." },
];

type Persistence = { transaction: boolean; decision: boolean; signals: number; audit: boolean; caseCreated: boolean };

export default function Simulator() {
  const [selected, setSelected] = useState("normal");
  const [result, setResult] = useState<RiskResult | null>(null);
  const [persistence, setPersistence] = useState<Persistence | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function run() {
    setLoading(true); setError(""); setResult(null); setPersistence(null);
    try {
      const decision = await runScenario(selected);
      setResult(decision);
      const [transactionResult, auditResult] = await Promise.allSettled([getTransaction(decision.transaction_id), getAuditEvents()]);
      const transaction = transactionResult.status === "fulfilled" ? transactionResult.value as unknown as { risk_decision?: unknown; risk_signals?: unknown[]; case_id?: string | null } : null;
      const audit = auditResult.status === "fulfilled" ? auditResult.value.items : [];
      setPersistence({
        transaction: transaction !== null,
        decision: Boolean(transaction?.risk_decision),
        signals: transaction?.risk_signals?.length ?? 0,
        audit: audit.some((event) => event.metadata?.transaction_id === decision.transaction_id || event.entity_id === decision.case_id),
        caseCreated: Boolean(transaction?.case_id),
      });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "TrustSentinel could not process this scenario.");
    } finally { setLoading(false); }
  }

  return <div className="app-shell"><Sidebar /><main className="main-content">
    <header className="page-header"><div><div className="eyebrow">SANDBOX / RISK EVALUATION</div><h1>Scenario lab</h1><p>Send a supported synthetic scenario to the live backend risk engine.</p></div><span className="data-source-label">BACKEND SCENARIOS</span></header>
    <div className="notice notice-info"><CircleAlert size={16} /><span>Scenarios create persisted synthetic records. They are not live payment data or real-world fraud evidence.</span></div>
    <div className="simulator-layout"><section className="card"><div className="section-heading"><div><div className="eyebrow">SCENARIO INPUT</div><h2>Choose a scenario</h2><p>Only identifiers supported by the current API are listed.</p></div></div><div className="scenario-grid">{scenarios.map((scenario) => <button type="button" key={scenario.id} aria-pressed={selected === scenario.id} className={`scenario-card${selected === scenario.id ? " selected" : ""}`} onClick={() => setSelected(scenario.id)}><span className="scenario-icon">{scenario.id === "normal" || scenario.id === "legitimate_high_value" ? <CheckCircle2 size={17} /> : <ShieldAlert size={17} />}</span><strong>{scenario.title}</strong><span>{scenario.description}</span></button>)}</div><button type="button" className="primary-button run-button" onClick={() => void run()} disabled={loading}>{loading ? <><Loader2 size={17} className="spin" /> Evaluating with API…</> : <><Play size={16} /> Run scenario</>}</button></section>
      <section className="card result-card" aria-live="polite"><div className="section-heading"><div><div className="eyebrow">API RESPONSE</div><h2>Risk decision</h2><p>Scores and action come from the backend response.</p></div></div>
        {loading && <div className="empty-state"><Loader2 size={20} className="spin" /> Waiting for the risk service…</div>}
        {error && <div className="notice notice-error" role="alert"><strong>Scenario failed</strong><span>{error}</span></div>}
        {!loading && !error && !result && <div className="empty-state"><ShieldAlert size={23} /><span>Select a scenario and submit it to get a real decision.</span></div>}
        {result && <><div className="result-score"><span>Hybrid risk score</span><strong>{result.risk_score}</strong><span className={`risk-tag risk-${result.risk_band.toLowerCase()}`}>{result.risk_band}</span></div><dl className="data-list"><div><dt>Recommended action</dt><dd>{result.recommended_action}</dd></div><div><dt>Rules score</dt><dd>{result.rule_score}</dd></div><div><dt>ML score</dt><dd>{result.ml_score === null ? "Unavailable" : result.ml_score.toFixed(3)}</dd></div><div><dt>ML runtime</dt><dd>{result.ml_status}</dd></div><div><dt>Model</dt><dd>{result.model_version}</dd></div><div><dt>Policy</dt><dd>{result.hybrid_policy_version}</dd></div><div><dt>Feature schema</dt><dd>{result.feature_schema_version}</dd></div><div><dt>Decision latency</dt><dd>{result.latency_ms} ms</dd></div></dl><div className="explanation"><h3>Explanation</h3><p>{result.explanation}</p></div><div className="explanation"><h3>Reason codes</h3>{result.reason_codes.length ? <div className="reason-list">{result.reason_codes.map((code) => <span key={code}>{code}</span>)}</div> : <p>No rule signals were triggered.</p>}</div><div className="explanation"><h3>Persisted signals</h3>{result.signals.length ? <div className="evidence-list">{result.signals.map((signal, index) => <div className="evidence-row" key={`${signal.signal_type}-${index}`}><strong>{signal.signal_type} · {signal.severity}</strong><p>{signal.evidence}</p><small>Source: {signal.source_feature}</small></div>)}</div> : <p>No signal evidence returned.</p>}</div><div className="explanation"><h3>Persistence verification</h3>{persistence ? <dl className="data-list"><div><dt>Transaction</dt><dd>{persistence.transaction ? "Verified" : "Not verified"}</dd></div><div><dt>Decision</dt><dd>{persistence.decision ? "Verified" : "Not verified"}</dd></div><div><dt>Signals</dt><dd>{persistence.signals} stored</dd></div><div><dt>Audit event</dt><dd>{persistence.audit ? "Found" : "Not found in latest 100 events"}</dd></div><div><dt>Case</dt><dd>{persistence.caseCreated ? result.case_id : "None created"}</dd></div></dl> : <p>Checking transaction and audit records…</p>}</div></>}
      </section></div>
  </main></div>;
}
