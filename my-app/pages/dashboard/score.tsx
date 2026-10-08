import { FormEvent, useState } from "react";
import Sidebar from "../../components/layout/Sidebar";
import { scoreTransaction, type RiskResult } from "../../lib/api";
import { Loader2, ShieldAlert } from "lucide-react";

export default function ScoreTransaction() {
  const [result, setResult] = useState<RiskResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setLoading(true); setError(""); setResult(null);
    try {
      const decision = await scoreTransaction({
        transaction_id: String(form.get("transaction_id")),
        account_id: String(form.get("account_id")),
        amount: Number(form.get("amount")),
        currency: String(form.get("currency")),
        beneficiary_id: String(form.get("beneficiary_id")),
        device_id: String(form.get("device_id")),
        channel: String(form.get("channel")) as "mobile_app" | "web" | "ussd" | "api",
      });
      setResult(decision);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "TrustSentinel could not score this transaction."); }
    finally { setLoading(false); }
  }

  return <div className="app-shell"><Sidebar /><main className="main-content">
    <header className="page-header"><div><div className="eyebrow">RISK OPERATIONS / TRANSACTION INTAKE</div><h1>Score a transaction</h1><p>Submit transaction facts to the backend rules and ML pipeline.</p></div><span className="data-source-label">LIVE RISK API</span></header>
    <div className="notice notice-info"><ShieldAlert size={16} /><span>Enter transaction facts directly. Previously unseen account, beneficiary, and device IDs are accepted and evaluated as new entities.</span></div>
    <div className="simulator-layout"><form className="card score-form" onSubmit={submit}><div className="eyebrow">TRANSACTION INPUT</div><h2>Payment context</h2><div className="form-grid"><label>Transaction ID<input name="transaction_id" required maxLength={100} autoComplete="off" /></label><label>Account ID<input name="account_id" required maxLength={80} autoComplete="off" /></label><label>Beneficiary ID<input name="beneficiary_id" required maxLength={80} autoComplete="off" /></label><label>Device ID<input name="device_id" required maxLength={80} autoComplete="off" /></label><label>Amount<input name="amount" type="number" min="0.01" max="1000000000" step="0.01" required /></label><label>Currency<input name="currency" defaultValue="NGN" minLength={3} maxLength={8} required /></label><label>Channel<select name="channel" defaultValue="mobile_app"><option value="mobile_app">Mobile app</option><option value="web">Web</option><option value="ussd">USSD</option><option value="api">API</option></select></label></div><button className="primary-button run-button" type="submit" disabled={loading}>{loading ? <><Loader2 size={16} className="spin" /> Sending to risk API…</> : "Evaluate transaction"}</button></form>
      <section className="card result-card" aria-live="polite"><div className="eyebrow">BACKEND DECISION</div><h2>Risk assessment</h2>{loading ? <div className="empty-state">Waiting for the risk service…</div> : error ? <div className="notice notice-error" role="alert"><strong>Scoring request failed</strong><span>{error}</span></div> : result ? <><div className="result-score"><span>Risk score</span><strong>{result.risk_score}</strong><span className={`risk-tag risk-${result.risk_band.toLowerCase()}`}>{result.risk_band}</span></div><dl className="data-list"><div><dt>Action</dt><dd>{result.recommended_action}</dd></div><div><dt>Rules score</dt><dd>{result.rule_score}</dd></div><div><dt>ML score / status</dt><dd>{result.ml_score === null ? "Unavailable" : result.ml_score.toFixed(3)} · {result.ml_status}</dd></div><div><dt>Model / policy</dt><dd>{result.model_version} · {result.hybrid_policy_version}</dd></div><div><dt>Latency</dt><dd>{result.latency_ms} ms</dd></div></dl><div className="explanation"><h3>Explanation</h3><p>{result.explanation}</p></div><div className="explanation"><h3>Reason codes</h3><p>{result.reason_codes.join(", ") || "No rule signals were triggered."}</p></div></> : <div className="empty-state">Submit transaction facts to receive a backend decision.</div>}</section></div>
  </main></div>;
}
