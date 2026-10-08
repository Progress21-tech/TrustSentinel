import Sidebar from "../../components/layout/Sidebar";
import {
  TrendingUp,
  ShieldCheck,
  AlertTriangle,
  Activity,
} from "lucide-react";

const riskDistribution = [
  { label: "LOW", value: 58, count: 1842 },
  { label: "MODERATE", value: 19, count: 604 },
  { label: "ELEVATED", value: 13, count: 413 },
  { label: "HIGH", value: 7, count: 222 },
  { label: "CRITICAL", value: 3, count: 96 },
];

const interventions = [
  { label: "ALLOW", value: 1842 },
  { label: "WARN", value: 604 },
  { label: "STEP-UP", value: 413 },
  { label: "HOLD", value: 222 },
  { label: "REVIEW", value: 96 },
];

export default function Metrics() {
  return (
    <div>
      <Sidebar />

      <main className="main-content">
        <div className="page-header">
          <div>
            <div className="eyebrow">EXECUTIVE ANALYTICS</div>
            <h1>Metrics</h1>
            <p>Operational performance from the synthetic TrustSentinel environment.</p>
          </div>

          <div className="status-pill">
            <span />
            SYNTHETIC DATA
          </div>
        </div>

        <div className="metrics-grid">
          <div className="card metric-large">
            <div className="metric-icon">
              <Activity size={18} />
            </div>
            <span>Transactions Evaluated</span>
            <strong>3,177</strong>
            <small>synthetic transactions</small>
          </div>

          <div className="card metric-large">
            <div className="metric-icon">
              <AlertTriangle size={18} />
            </div>
            <span>High-Risk Transactions</span>
            <strong>318</strong>
            <small>HIGH + CRITICAL</small>
          </div>

          <div className="card metric-large">
            <div className="metric-icon">
              <ShieldCheck size={18} />
            </div>
            <span>Interventions</span>
            <strong>1,335</strong>
            <small>WARN + STEP-UP + HOLD + REVIEW</small>
          </div>

          <div className="card metric-large">
            <div className="metric-icon">
              <TrendingUp size={18} />
            </div>
            <span>Avg Decision Time</span>
            <strong>42ms</strong>
            <small>risk engine latency</small>
          </div>
        </div>

        <div className="metrics-content-grid">
          <section className="card">
            <div className="section-heading">
              <div>
                <h2>Risk Distribution</h2>
                <p>Distribution of evaluated synthetic transactions.</p>
              </div>
            </div>

            <div className="distribution-list">
              {riskDistribution.map((item) => (
                <div className="distribution-row" key={item.label}>
                  <div className="distribution-header">
                    <strong>{item.label}</strong>
                    <span>{item.count}</span>
                  </div>

                  <div className="distribution-track">
                    <div
                      className={`distribution-bar bar-${item.label.toLowerCase()}`}
                      style={{ width: `${item.value}%` }}
                    />
                  </div>

                  <small>{item.value}%</small>
                </div>
              ))}
            </div>
          </section>

          <section className="card">
            <div className="section-heading">
              <div>
                <h2>Intervention Mix</h2>
                <p>Recommended actions returned by the engine.</p>
              </div>
            </div>

            <div className="intervention-list">
              {interventions.map((item) => (
                <div className="intervention-row" key={item.label}>
                  <span>{item.label}</span>
                  <strong>{item.value.toLocaleString()}</strong>
                </div>
              ))}
            </div>
          </section>
        </div>

        <section className="card synthetic-notice">
          <ShieldCheck size={18} />

          <div>
            <strong>Demo analytics only</strong>
            <p>
              All metrics shown here are based on synthetic sandbox activity.
              They must not be interpreted as production fraud-loss,
              customer-impact, or financial-performance measurements.
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}