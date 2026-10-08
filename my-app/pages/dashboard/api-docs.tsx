import Sidebar from "../../components/layout/Sidebar";
import { Code2 } from "lucide-react";

const endpoints = [
  ["POST", "/v1/auth/login", "Verify analyst credentials and issue a time-limited bearer session."],
  ["GET", "/v1/auth/session", "Verify the current signed analyst session."],
  ["GET", "/health", "Read API liveness."],
  ["GET", "/ready", "Read database and model readiness metadata."],
  ["POST", "/v1/risk/score", "Score a transaction using backend rules and loaded ML inference."],
  ["POST", "/v1/sandbox/scenario", "Run a backend-supported synthetic scenario."],
  ["GET", "/v1/transactions?limit=50", "List persisted transactions and their decisions."],
  ["GET", "/v1/transactions/{id}", "Read one persisted transaction, decision, signals, and case reference."],
  ["GET", "/v1/cases", "List persisted risk investigation cases."],
  ["GET", "/v1/cases/{id}", "Read a case, evidence, and its audit timeline."],
  ["POST", "/v1/cases/{id}/outcome", "Persist an analyst outcome and its audit event."],
  ["GET", "/v1/audit?limit=100", "List persisted audit events."],
  ["GET", "/v1/metrics/summary", "Read aggregate metrics from persisted backend records."],
];

export default function ApiDocs() {
  return <div className="app-shell"><Sidebar /><main className="main-content">
    <header className="page-header"><div><div className="eyebrow">INTEGRATION / REFERENCE</div><h1>API reference</h1><p>Backend routes currently used by the TrustSentinel analyst workspace.</p></div><span className="data-source-label">CONTRACT REFERENCE</span></header>
    <section className="card table-card"><div className="section-heading"><div><h2>Backend endpoints</h2><p>Protected routes use the signed bearer session from analyst sign-in.</p></div></div><div className="table-wrap"><table><thead><tr><th>Method</th><th>Path</th><th>Purpose</th></tr></thead><tbody>{endpoints.map(([method, path, description]) => <tr key={`${method}-${path}`}><td><span className="case-status">{method}</span></td><td><code>{path}</code></td><td>{description}</td></tr>)}</tbody></table></div></section>
    <section className="card api-note"><Code2 size={17} /><div><h2>Response integrity</h2><p>Risk score, band, action, rules score, ML score, reason codes, and model metadata are rendered from backend responses. The frontend does not calculate risk or substitute sample responses.</p><p>Authentication requires backend configuration for <code>ANALYST_EMAIL</code>, a PBKDF2 password hash, and <code>SESSION_SIGNING_SECRET</code>. Liveness and readiness remain public; business APIs require a valid session or configured backend API key.</p></div></section>
  </main></div>;
}
