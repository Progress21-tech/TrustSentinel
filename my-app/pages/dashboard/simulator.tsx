import { useState } from "react";
import Sidebar from "../../components/layout/Sidebar";
import { Play, ShieldAlert, CheckCircle2, Loader2 } from "lucide-react";
import { runScenario } from "../../lib/api";

const scenarios = [
  {
    id: "normal",
    title: "Normal Payment",
    description: "Routine customer payment with no unusual signals.",
  },
  {
    id: "new_beneficiary_large_amount",
    title: "New Beneficiary + Unusual Amount",
    description: "First-time beneficiary combined with an unusual payment amount.",
  },
  {
    id: "new_device_large_transfer",
    title: "New Device + High-Value Transfer",
    description: "Recent device change followed by a high-value transfer.",
  },
  {
    id: "account_recovery_new_beneficiary",
    title: "Recovery + New Beneficiary",
    description: "Recent account recovery followed by a new beneficiary payment.",
  },
  {
    id: "rapid_transfers",
    title: "Rapid Transfers",
    description: "Multiple transfers within a short period.",
  },
  {
    id: "risky_beneficiary",
    title: "Risky Beneficiary / Network",
    description: "Payment involving a beneficiary with synthetic risk history.",
  },
  {
    id: "combined_high_risk",
    title: "Combined High-Risk Scenario",
    description: "Multiple high-risk contextual indicators occurring together.",
  },
  {
    id: "legitimate_high_value",
    title: "Legitimate High-Value Payment",
    description: "High-value payment with otherwise legitimate context.",
  },
];

export default function Simulator() {
  const [selectedScenario, setSelectedScenario] = useState("normal");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");

  async function handleRunScenario() {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await runScenario(selectedScenario);
      setResult(data);
    } catch {
      setError(
        "Backend unavailable. The simulator is ready, but the TrustSentinel API has not been connected yet."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <Sidebar />

      <main className="main-content">
        <div className="page-header">
          <div>
            <div className="eyebrow">SANDBOX ENVIRONMENT</div>
            <h1>Payment Simulator</h1>
            <p>
              Run deterministic synthetic scenarios through the TrustSentinel
              risk engine.
            </p>
          </div>

          <div className="status-pill">
            <span />
            SYNTHETIC DATA
          </div>
        </div>

        <div className="simulator-layout">
          <section className="card">
            <div className="section-heading">
              <div>
                <h2>Select Scenario</h2>
                <p>Choose a predefined payment scenario.</p>
              </div>
            </div>

            <div className="scenario-grid">
              {scenarios.map((scenario) => (
                <button
                  key={scenario.id}
                  className={`scenario-card ${
                    selectedScenario === scenario.id ? "selected" : ""
                  }`}
                  onClick={() => setSelectedScenario(scenario.id)}
                >
                  <div className="scenario-icon">
                    {scenario.id === "normal" ||
                    scenario.id === "legitimate_high_value" ? (
                      <CheckCircle2 size={18} />
                    ) : (
                      <ShieldAlert size={18} />
                    )}
                  </div>

                  <strong>{scenario.title}</strong>
                  <span>{scenario.description}</span>
                </button>
              ))}
            </div>

            <button
              className="run-button"
              onClick={handleRunScenario}
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 size={18} className="spin" />
                  Evaluating...
                </>
              ) : (
                <>
                  <Play size={18} />
                  Run Scenario
                </>
              )}
            </button>
          </section>

          <section className="card result-card">
            <div className="section-heading">
              <div>
                <h2>Payment Decision</h2>
                <p>Backend risk decision</p>
              </div>
            </div>

            {!result && !error && !loading && (
              <div className="empty-result">
                <ShieldAlert size={30} />
                <strong>No decision yet</strong>
                <span>
                  Select a scenario and run it to evaluate the synthetic
                  payment.
                </span>
              </div>
            )}

            {loading && (
              <div className="empty-result">
                <Loader2 size={30} className="spin" />
                <strong>Evaluating payment...</strong>
                <span>
                  Waiting for the TrustSentinel risk engine response.
                </span>
              </div>
            )}

            {error && (
              <div className="error-state">
                <ShieldAlert size={22} />
                <strong>Backend unavailable</strong>
                <p>{error}</p>
              </div>
            )}

            {result && (
              <div className="decision-result">
                <div className="decision-score">
                  <span>Risk Score</span>
                  <strong>{result.risk_score}</strong>
                </div>

                <div className="decision-row">
                  <span>Risk Band</span>
                  <strong>{result.risk_band}</strong>
                </div>

                <div className="decision-row">
                  <span>Recommended Action</span>
                  <strong>{result.recommended_action}</strong>
                </div>

                {result.explanation && (
                  <div className="explanation">
                    <span>Why this changed</span>
                    <p>{result.explanation}</p>
                  </div>
                )}

                {result.reason_codes?.length > 0 && (
                  <div className="reasons">
                    <span>Risk Indicators</span>

                    <div className="reason-list">
                      {result.reason_codes.map((reason: string) => (
                        <span key={reason}>{reason}</span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="synthetic-label">
                  SYNTHETIC DEMO TRANSACTION
                </div>
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}