import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import Sidebar from "../../components/layout/Sidebar";
import { getTransactions } from "../../lib/api";
import { Search, SlidersHorizontal } from "lucide-react";

type TransactionItem = Awaited<ReturnType<typeof getTransactions>>["items"][number];

export default function Transactions() {
  const [items, setItems] = useState<TransactionItem[] | null>(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [band, setBand] = useState("ALL");
  const [loading, setLoading] = useState(true);
  useEffect(() => { getTransactions(200).then((result) => setItems(result.items)).catch((reason) => setError(reason instanceof Error ? reason.message : "Unable to load transactions.")).finally(() => setLoading(false)); }, []);

  const filtered = useMemo(() => (items ?? []).filter((item) => {
    const decision = item.risk_decision as { risk_band?: string } | null;
    return String(item.transaction_id).toLowerCase().includes(search.toLowerCase()) && (band === "ALL" || decision?.risk_band === band);
  }), [items, search, band]);

  return <div className="app-shell"><Sidebar /><main className="main-content">
    <header className="page-header"><div><div className="eyebrow">RISK OPERATIONS / RECORDS</div><h1>Transactions</h1><p>Persisted transaction decisions returned by the TrustSentinel API.</p></div><span className="data-source-label">BACKEND DATA</span></header>
    <section className="card filter-bar"><label className="search-box"><Search size={16} /><span className="sr-only">Search by transaction ID</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search transaction ID" /></label><label className="filter-select"><SlidersHorizontal size={15} /><span className="sr-only">Filter by risk band</span><select value={band} onChange={(event) => setBand(event.target.value)}><option value="ALL">All risk bands</option>{["LOW", "MODERATE", "ELEVATED", "HIGH", "CRITICAL"].map((value) => <option key={value}>{value}</option>)}</select></label><span className="muted-copy">{items?.length ?? 0} records loaded</span></section>
    <section className="card table-card"><div className="section-heading"><div><h2>Transaction history</h2><p>Latest 200 records</p></div></div>
      {loading ? <div className="empty-state">Loading transactions…</div> : error ? <div className="empty-state error-copy" role="alert">Unable to load TrustSentinel transactions: {error}</div> : filtered.length === 0 ? <div className="empty-state">{items?.length ? "No transactions match these filters." : "No persisted transactions are available."}</div> : <div className="table-wrap"><table><thead><tr><th>Transaction</th><th>Account</th><th>Amount</th><th>Score</th><th>Risk band</th><th>Action</th><th>Signals</th><th>Recorded</th></tr></thead><tbody>{filtered.map((item) => {
        const decision = item.risk_decision as { risk_score: number; risk_band: string; recommended_action: string } | null;
        const signals = item.signals as string[];
        return <tr key={String(item.transaction_id)}><td><Link className="table-link" href={`/dashboard/transactions/${encodeURIComponent(String(item.transaction_id))}`}>{String(item.transaction_id)}</Link></td><td>{String(item.account_id)}</td><td>{String(item.currency)} {Number(item.amount).toLocaleString()}</td><td>{decision?.risk_score ?? "—"}</td><td>{decision ? <span className={`risk-tag risk-${decision.risk_band.toLowerCase()}`}>{decision.risk_band}</span> : "—"}</td><td>{decision?.recommended_action ?? "—"}</td><td>{signals?.length ? signals.join(", ") : "None recorded"}</td><td>{item.timestamp ? new Date(String(item.timestamp)).toLocaleString() : "—"}</td></tr>;
      })}</tbody></table></div>}
    </section>
  </main></div>;
}
