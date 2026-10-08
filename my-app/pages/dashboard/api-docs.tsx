import Sidebar from "../../components/layout/Sidebar";
import {
  Activity,
  CheckCircle2,
  Code2,
  Server,
  ShieldCheck,
} from "lucide-react";

const endpoints = [
  {
    method: "GET",
    path: "/health",
    description: "Check whether the risk service is available.",
  },
  {
    method: "GET",
    path: "/ready",
    description: "Check whether the service is ready to process requests.",
  },
  {
    method: "POST",
    path: "/v1/risk/score",
    description: "Evaluate a transaction and return its risk decision.",
  },
  {
    method: "POST",
    path: "/v1/sandbox/scenario",
    description: "Run one of the predefined synthetic fraud scenarios.",
  },
  {
    method: "GET",
    path: "/v1/transactions/{id}",
    description: "Retrieve the risk assessment for a transaction.",
  },
  {
    method: "GET",
    path: "/v1/cases",
    description: "Retrieve fraud-risk investigation cases.",
  },
  {
    method: "GET",
    path: "/v1/cases/{id}",
    description: "Retrieve a specific investigation case.",
  },
  {
    method: "POST",
    path: "/v1/cases/{id}/outcome",
    description: "Record an analyst outcome for a case.",
  },
  {
    method: "GET",
    path: "/v1/metrics/summary",
    description: "Retrieve aggregate synthetic operational metrics.",
  },
];

const responseFields = [
  "transaction_id",
  "risk_score",
  "risk_band",
  "recommended_action",
  "reason_codes",
  "explanation",
  "model_version",
  "latency_ms",
];

export default function ApiDocs() {
  return (
    <div>
      <Sidebar />

      <main className="main-content">
        <div className="page-header">
          <div>
            <div className="eyebrow">DEVELOPER INTERFACE</div>
            <h1>API Documentation</h1>
            <p>
              TrustSentinel risk-engine endpoints and response contracts.
            </p>
          </div>

          <div className="status-pill">
            <span />
            SYNTHETIC ENVIRONMENT
          </div>
        </div>

        <div className="api-status-grid">
          <div className="card api-status-card">
            <div className="api-status-icon">
              <Server size={18} />
            </div>
            <div>
              <span>Risk Engine</span>
              <strong>FastAPI</strong>
            </div>
          </div>

          <div className="card api-status-card">
            <div className="api-status-icon">
              <Activity size={18} />
            </div>
            <div>
              <span>Decision Engine</span>
              <strong>Hybrid Rules + ML</strong>
            </div>
          </div>

          <div className="card api-status-card">
            <div className="api-status-icon">
              <ShieldCheck size={18} />
            </div>
            <div>
              <span>Environment</span>
              <strong>Synthetic Demo</strong>
            </div>
          </div>
        </div>

        <section className="card api-section">
          <div className="section-heading">
            <div>
              <h2>Endpoints</h2>
              <p>Available TrustSentinel backend operations.</p>
            </div>
          </div>

          <div className="endpoint-list">
            {endpoints.map((endpoint) => (
              <div className="endpoint-row" key={`${endpoint.method}-${endpoint.path}`}>
                <span className={`method method-${endpoint.method.toLowerCase()}`}>
                  {endpoint.method}
                </span>

                <code>{endpoint.path}</code>

                <p>{endpoint.description}</p>
              </div>
            ))}
          </div>
        </section>

        <div className="api-two-column">
          <section className="card api-section">
            <div className="section-heading">
              <div>
                <h2>Risk Response</h2>
                <p>Primary fields returned by the risk engine.</p>
              </div>
            </div>

            <div className="response-fields">
              {responseFields.map((field) => (
                <div className="response-field" key={field}>
                  <CheckCircle2 size={13} />
                  <code>{field}</code>
                </div>
              ))}
            </div>
          </section>

          <section className="card api-section">
            <div className="section-heading">
              <div>
                <h2>Example Response</h2>
                <p>Illustrative synthetic risk decision.</p>
              </div>
            </div>

            <pre className="api-code">
{`{
  "transaction_id": "txn_demo_001",
  "risk_score": 91,
  "risk_band": "CRITICAL",
  "recommended_action": "HOLD",
  "reason_codes": [
    "NEW_BENEFICIARY",
    "ABNORMAL_AMOUNT",
    "RECENT_DEVICE_CHANGE",
    "VELOCITY_SPIKE"
  ],
  "explanation":
    "Payment shows multiple signals associated with social-engineering risk.",
  "model_version": "risk-engine-v0.1",
  "latency_ms": 42
}`}
            </pre>
          </section>
        </div>

        <section className="card api-notice">
          <Code2 size={18} />

          <div>
            <strong>Backend is the source of truth</strong>
            <p>
              The frontend does not calculate risk scores, risk bands,
              recommended actions, reason codes, or model outputs. These values
              are returned directly by the TrustSentinel risk engine.
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}