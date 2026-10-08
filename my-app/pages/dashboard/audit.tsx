import Sidebar from "../../components/layout/Sidebar";
import {
  CheckCircle2,
  Clock3,
  FileText,
  ShieldAlert,
  UserCheck,
} from "lucide-react";

const auditEvents = [
  {
    time: "20:14:32",
    type: "RISK_DECISION",
    transaction: "txn_00841",
    action: "HOLD",
    actor: "Risk Engine",
    detail: "CRITICAL risk decision returned with 4 supporting signals.",
  },
  {
    time: "20:14:35",
    type: "CASE_CREATED",
    transaction: "txn_00841",
    action: "REVIEW",
    actor: "TrustSentinel",
    detail: "Case case_00421 created for analyst investigation.",
  },
  {
    time: "20:11:08",
    type: "RISK_DECISION",
    transaction: "txn_00840",
    action: "STEP-UP",
    actor: "Risk Engine",
    detail: "ELEVATED risk decision returned.",
  },
  {
    time: "20:08:41",
    type: "CASE_OUTCOME",
    transaction: "txn_00832",
    action: "CONFIRMED_SCAM",
    actor: "J. Analyst",
    detail: "Case marked as confirmed scam.",
  },
  {
    time: "20:03:17",
    type: "RISK_DECISION",
    transaction: "txn_00839",
    action: "ALLOW",
    actor: "Risk Engine",
    detail: "LOW risk decision returned.",
  },
];

function eventIcon(type: string) {
  if (type === "RISK_DECISION") {
    return <ShieldAlert size={15} />;
  }

  if (type === "CASE_OUTCOME") {
    return <UserCheck size={15} />;
  }

  return <FileText size={15} />;
}

export default function AuditLog() {
  return (
    <div>
      <Sidebar />

      <main className="main-content">
        <div className="page-header">
          <div>
            <div className="eyebrow">AUDIT & TRACEABILITY</div>
            <h1>Audit Log</h1>
            <p>
              Trace synthetic risk decisions, case events, and analyst actions.
            </p>
          </div>

          <div className="status-pill">
            <span />
            SYNTHETIC DATA
          </div>
        </div>

        <section className="card audit-summary">
          <div className="audit-summary-item">
            <Clock3 size={17} />
            <div>
              <span>Events Today</span>
              <strong>2,481</strong>
            </div>
          </div>

          <div className="audit-summary-item">
            <CheckCircle2 size={17} />
            <div>
              <span>Decisions Recorded</span>
              <strong>2,104</strong>
            </div>
          </div>

          <div className="audit-summary-item">
            <UserCheck size={17} />
            <div>
              <span>Analyst Actions</span>
              <strong>377</strong>
            </div>
          </div>
        </section>

        <section className="card audit-section">
          <div className="section-heading">
            <div>
              <h2>Recent Events</h2>
              <p>Most recent events recorded by the demo environment.</p>
            </div>
          </div>

          <div className="audit-list">
            {auditEvents.map((event, index) => (
              <div className="audit-row" key={`${event.time}-${index}`}>
                <div className="audit-icon">{eventIcon(event.type)}</div>

                <div className="audit-time">{event.time}</div>

                <div className="audit-event">
                  <div className="audit-event-top">
                    <strong>{event.type}</strong>

                    <span
                      className={`action-badge action-${event.action
                        .toLowerCase()
                        .replace("-", "")}`}
                    >
                      {event.action}
                    </span>
                  </div>

                  <div className="audit-meta">
                    <span>{event.transaction}</span>
                    <span>{event.actor}</span>
                  </div>

                  <p>{event.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="card audit-notice">
          <FileText size={17} />

          <div>
            <strong>Audit records are demonstration data</strong>
            <p>
              These events represent synthetic activity for the hackathon
              environment and do not represent production financial records.
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}