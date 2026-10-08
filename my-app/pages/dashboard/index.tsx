import Sidebar from "../../components/layout/Sidebar";
import {
  ShieldAlert,
  ShieldCheck,
  Clock3,
  Banknote,
  ArrowUpRight,
  AlertTriangle,
} from "lucide-react";

const transactions = [
  {
    id: "txn_00841",
    customer: "ACCT-20491",
    amount: "₦850,000",
    score: 91,
    band: "CRITICAL",
    action: "HOLD",
    time: "2 min ago",
  },
  {
    id: "txn_00840",
    customer: "ACCT-11872",
    amount: "₦240,000",
    score: 72,
    band: "ELEVATED",
    action: "STEP-UP",
    time: "5 min ago",
  },
  {
    id: "txn_00839",
    customer: "ACCT-77102",
    amount: "₦45,000",
    score: 18,
    band: "LOW",
    action: "ALLOW",
    time: "8 min ago",
  },
  {
    id: "txn_00838",
    customer: "ACCT-39184",
    amount: "₦310,000",
    score: 54,
    band: "MODERATE",
    action: "WARN",
    time: "12 min ago",
  },
];

export default function Dashboard() {
  return (
    <div>
      <Sidebar />

      <main className="main-content">
        <div className="page-header">
          <div>
            <div className="eyebrow">FRAUD OPERATIONS</div>
            <h1>Executive Overview</h1>
            <p>Real-time social engineering risk monitoring</p>
          </div>

          <div className="status-pill">
            <span />
            Risk engine operational
          </div>
        </div>

        <section className="metric-grid">
          <div className="metric-card">
            <div className="metric-icon">
              <ShieldAlert size={20} />
            </div>
            <span className="metric-label">High-Risk Payments</span>
            <strong>24</strong>
            <small>+12.5% today</small>
          </div>

          <div className="metric-card">
            <div className="metric-icon">
              <ShieldCheck size={20} />
            </div>
            <span className="metric-label">Payments Allowed</span>
            <strong>1,842</strong>
            <small>94.2% of volume</small>
          </div>

          <div className="metric-card">
            <div className="metric-icon">
              <Banknote size={20} />
            </div>
            <span className="metric-label">Prevented Loss</span>
            <strong>₦8.4M</strong>
            <small>Estimated today</small>
          </div>

          <div className="metric-card">
            <div className="metric-icon">
              <Clock3 size={20} />
            </div>
            <span className="metric-label">Avg Decision Time</span>
            <strong>42ms</strong>
            <small>Target &lt;100ms</small>
          </div>
        </section>

        <section className="dashboard-grid">
          <div className="card">
            <div className="section-heading">
              <div>
                <h2>Recent Risk Decisions</h2>
                <p>Latest payment evaluations</p>
              </div>
              <ArrowUpRight size={18} />
            </div>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Transaction</th>
                    <th>Account</th>
                    <th>Amount</th>
                    <th>Risk</th>
                    <th>Action</th>
                    <th>Time</th>
                  </tr>
                </thead>

                <tbody>
                  {transactions.map((tx) => (
                    <tr key={tx.id}>
                      <td>{tx.id}</td>
                      <td>{tx.customer}</td>
                      <td>{tx.amount}</td>
                      <td>
                        <span className={`risk-score score-${tx.band.toLowerCase()}`}>
                          {tx.score}
                        </span>
                      </td>
                      <td>
                        <span className={`action-badge action-${tx.action.toLowerCase().replace("-", "")}`}>
                          {tx.action}
                        </span>
                      </td>
                      <td>{tx.time}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="card alerts-card">
            <div className="section-heading">
              <div>
                <h2>Risk Signals</h2>
                <p>Most active signals today</p>
              </div>
              <AlertTriangle size={18} />
            </div>

            <div className="signal-list">
              <div className="signal-row">
                <div>
                  <strong>NEW_BENEFICIARY</strong>
                  <span>First-time beneficiary</span>
                </div>
                <b>31</b>
              </div>

              <div className="signal-row">
                <div>
                  <strong>ABNORMAL_AMOUNT</strong>
                  <span>Amount deviation</span>
                </div>
                <b>24</b>
              </div>

              <div className="signal-row">
                <div>
                  <strong>DEVICE_CHANGE</strong>
                  <span>Recent device change</span>
                </div>
                <b>18</b>
              </div>

              <div className="signal-row">
                <div>
                  <strong>VELOCITY_SPIKE</strong>
                  <span>Rapid transaction burst</span>
                </div>
                <b>13</b>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}