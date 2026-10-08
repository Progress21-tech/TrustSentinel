import { useRouter } from "next/router";
import Link from "next/link";
import { useState } from "react";
import Sidebar from "../../../components/layout/Sidebar";
import {
  ArrowLeft,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Clock3,
  UserRound,
} from "lucide-react";

export default function CaseDetail() {
  const router = useRouter();
  const { id } = router.query;

  const [status, setStatus] = useState("OPEN");
  const [outcome, setOutcome] = useState("PENDING");
  const [notes, setNotes] = useState("");

  function handleOutcome(nextOutcome: string) {
    setOutcome(nextOutcome);
    setStatus("CLOSED");
  }

  return (
    <div>
      <Sidebar />

      <main className="main-content">
        <Link href="/dashboard/cases" className="back-link">
          <ArrowLeft size={15} />
          Back to Cases
        </Link>

        <div className="page-header">
          <div>
            <div className="eyebrow">CASE INVESTIGATION</div>
            <h1>{id || "case_00421"}</h1>
            <p>Analyst review of a synthetic high-risk transaction.</p>
          </div>

          <div className="status-pill">
            <span />
            SYNTHETIC DATA
          </div>
        </div>

        <section className="case-summary-grid">
          <div className="card">
            <span className="detail-label">Transaction</span>
            <strong>txn_00841</strong>
          </div>

          <div className="card">
            <span className="detail-label">Risk Score</span>
            <strong className="case-score">91</strong>
          </div>

          <div className="card">
            <span className="detail-label">Risk Band</span>
            <strong className="critical-text">CRITICAL</strong>
          </div>

          <div className="card">
            <span className="detail-label">Action</span>
            <strong className="hold-text">HOLD</strong>
          </div>
        </section>

        <div className="case-detail-grid">
          <section className="card">
            <div className="section-heading">
              <div>
                <h2>Risk Evidence</h2>
                <p>Signals returned by the TrustSentinel risk engine.</p>
              </div>
            </div>

            <div className="assessment-banner">
              <ShieldAlert size={22} />

              <div>
                <strong>Multiple high-risk indicators detected</strong>
                <p>
                  Payment shows multiple signals associated with
                  social-engineering risk.
                </p>
              </div>
            </div>

            <div className="case-evidence-grid">
              <div>
                <span>NEW_BENEFICIARY</span>
                <p>Beneficiary is new to the customer.</p>
              </div>

              <div>
                <span>ABNORMAL_AMOUNT</span>
                <p>Payment amount differs significantly from normal activity.</p>
              </div>

              <div>
                <span>RECENT_DEVICE_CHANGE</span>
                <p>Recent device change detected before payment.</p>
              </div>

              <div>
                <span>VELOCITY_SPIKE</span>
                <p>Multiple transfers occurred within a short period.</p>
              </div>
            </div>
          </section>

          <section className="card">
            <div className="section-heading">
              <div>
                <h2>Case Status</h2>
                <p>Current investigation state.</p>
              </div>
            </div>

            <div className="case-status-box">
              <span>Status</span>
              <strong className={status === "OPEN" ? "case-status-open" : "case-status-closed"}>
                {status}
              </strong>
            </div>

            <div className="case-status-box">
              <span>Outcome</span>
              <strong>{outcome}</strong>
            </div>

            <div className="case-status-box">
              <span>Analyst</span>
              <strong className="analyst-name">
                <UserRound size={14} />
                Demo Analyst
              </strong>
            </div>
          </section>
        </div>

        <section className="card analyst-action-card">
          <div className="section-heading">
            <div>
              <h2>Analyst Decision</h2>
              <p>Record the investigation outcome for this synthetic case.</p>
            </div>
          </div>

          {status === "OPEN" ? (
            <>
              <div className="outcome-actions">
                <button
                  className="outcome-button scam"
                  onClick={() => handleOutcome("CONFIRMED_SCAM")}
                >
                  <ShieldAlert size={17} />
                  Confirm Scam
                </button>

                <button
                  className="outcome-button legitimate"
                  onClick={() => handleOutcome("LEGITIMATE")}
                >
                  <CheckCircle2 size={17} />
                  Mark Legitimate
                </button>

                <button
                  className="outcome-button dismiss"
                  onClick={() => handleOutcome("DISMISSED")}
                >
                  <XCircle size={17} />
                  Dismiss Case
                </button>
              </div>

              <div className="notes-area">
                <label htmlFor="notes">Analyst Notes</label>

                <textarea
                  id="notes"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Add investigation notes..."
                />
              </div>
            </>
          ) : (
            <div className="case-closed-banner">
              <CheckCircle2 size={20} />

              <div>
                <strong>Case closed</strong>
                <p>
                  Outcome recorded as <b>{outcome}</b>.
                </p>
              </div>
            </div>
          )}
        </section>

        <section className="card case-timeline-card">
          <div className="section-heading">
            <div>
              <h2>Case Timeline</h2>
              <p>Investigation activity.</p>
            </div>
          </div>

          <div className="timeline">
            <div className="timeline-item">
              <div className="timeline-dot" />

              <div>
                <strong>Case created</strong>
                <span>Risk engine created an investigation case.</span>
              </div>

              <time>
                <Clock3 size={12} />
                2 min ago
              </time>
            </div>

            <div className="timeline-item">
              <div className="timeline-dot" />

              <div>
                <strong>Payment placed on hold</strong>
                <span>Recommended action: HOLD.</span>
              </div>

              <time>Immediately</time>
            </div>

            {status === "CLOSED" && (
              <div className="timeline-item">
                <div className="timeline-dot" />

                <div>
                  <strong>Analyst outcome recorded</strong>
                  <span>{outcome}</span>
                </div>

                <time>Now</time>
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}