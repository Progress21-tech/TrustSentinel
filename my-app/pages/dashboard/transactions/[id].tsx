import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Link from "next/link";
import Sidebar from "../../../components/layout/Sidebar";
import { getTransaction } from "../../../lib/api";
import { ArrowLeft } from "lucide-react";

type TransactionDetail = {
  transaction: { transaction_id: string; account_id: string; beneficiary_id: string; device_id: string; amount: number; currency: string; channel: string; status: string; timestamp: string };
  risk_signals: Array<{ signal_type: string; severity: number; source_feature: string; signal_value: number; evidence: string }>;
  risk_decision: { risk_score: number; risk_band: string; recommended_action: string; reason_codes: string[]; explanation: string } | null;
  intervention: { action: string; customer_response: string | null } | null;
  case_id: string | null;
};

export default function TransactionDetail() {
  const router = useRouter();
  const id = typeof router.query.id === "string" ? router.query.id : "";
  const [record, setRecord] = useState<TransactionDetail | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => { if (!id) return; getTransaction(id).then((data) => setRecord(data as unknown as TransactionDetail)).catch((reason) => setError(reason instanceof Error ? reason.message : "Unable to load transaction.")).finally(() => setLoading(false)); }, [id]);
  return <div className="app-shell"><Sidebar /><main className="main-content"><Link href="/dashboard/transactions" className="back-link"><ArrowLeft size={15} /> Back to transactions</Link><header className="page-header"><div><div className="eyebrow">RISK OPERATIONS / TRANSACTION</div><h1>{id || "Transaction"}</h1><p>Persisted transaction details and risk evidence.</p></div><span className="data-source-label">LIVE API DATA</span></header>
    {loading ? <section className="card empty-state">Loading transaction record…</section> : error ? <section className="card empty-state error-copy" role="alert">Unable to load transaction: {error}</section> : record && <>
      <section className="metric-grid metric-grid-three"><article className="metric-card"><div className="metric-card-top"><span>Amount</span></div><strong>{record.transaction.currency} {record.transaction.amount.toLocaleString()}</strong><small>{record.transaction.channel}</small></article><article className="metric-card"><div className="metric-card-top"><span>Risk score</span></div><strong>{record.risk_decision?.risk_score ?? "Unavailable"}</strong><small>{record.risk_decision?.risk_band ?? "No risk decision"}</small></article><article className="metric-card"><div className="metric-card-top"><span>Recommendation</span></div><strong>{record.risk_decision?.recommended_action ?? "Unavailable"}</strong><small>Transaction status: {record.transaction.status}</small></article></section>
      <section className="dashboard-grid case-content-grid"><article className="card"><div className="eyebrow">TRANSACTION CONTEXT</div><h2>Recorded identifiers</h2><dl className="data-list"><div><dt>Account</dt><dd>{record.transaction.account_id}</dd></div><div><dt>Beneficiary</dt><dd>{record.transaction.beneficiary_id}</dd></div><div><dt>Device</dt><dd>{record.transaction.device_id}</dd></div><div><dt>Timestamp</dt><dd>{new Date(record.transaction.timestamp).toLocaleString()}</dd></div></dl></article><article className="card"><div className="eyebrow">RISK EXPLANATION</div><h2>Backend decision</h2><p>{record.risk_decision?.explanation ?? "No decision explanation is available."}</p><p>Reason codes: {record.risk_decision?.reason_codes.join(", ") || "None recorded"}</p>{record.case_id && <Link className="table-link" href={`/dashboard/cases/${encodeURIComponent(record.case_id)}`}>Open case {record.case_id}</Link>}</article></section>
      <section className="card"><div className="section-heading"><div className="eyebrow">PERSISTED SIGNALS</div><h2>Risk evidence</h2></div>{record.risk_signals.length ? <div className="evidence-list">{record.risk_signals.map((signal, index) => <article className="evidence-row" key={`${signal.signal_type}-${index}`}><span className="risk-tag risk-elevated">{signal.signal_type}</span><strong>{signal.severity} pts</strong><p>{signal.evidence}</p><small>{signal.source_feature}: {signal.signal_value}</small></article>)}</div> : <div className="empty-state">No risk signal rows were persisted for this transaction.</div>}</section>
    </>}
  </main></div>;
}
