import { useMemo, useState } from "react";
import Link from "next/link";
import Sidebar from "../../components/layout/Sidebar";
import { Search, SlidersHorizontal } from "lucide-react";

const transactions = [
  {
    id: "txn_00841",
    amount: "₦1,850,000",
    score: 91,
    band: "CRITICAL",
    action: "HOLD",
    signals: ["NEW_BENEFICIARY", "ABNORMAL_AMOUNT", "DEVICE_CHANGE", "VELOCITY_SPIKE"],
    time: "2 min ago",
    caseStatus: "OPEN",
  },
  {
    id: "txn_00840",
    amount: "₦640,000",
    score: 72,
    band: "ELEVATED",
    action: "STEP-UP",
    signals: ["NEW_BENEFICIARY", "ABNORMAL_AMOUNT"],
    time: "8 min ago",
    caseStatus: "OPEN",
  },
  {
    id: "txn_00839",
    amount: "₦45,000",
    score: 18,
    band: "LOW",
    action: "ALLOW",
    signals: ["NORMAL_PATTERN"],
    time: "14 min ago",
    caseStatus: "NONE",
  },
  {
    id: "txn_00838",
    amount: "₦280,000",
    score: 54,
    band: "MODERATE",
    action: "WARN",
    signals: ["UNUSUAL_AMOUNT", "NEW_BENEFICIARY"],
    time: "21 min ago",
    caseStatus: "NONE",
  },
  {
    id: "txn_00837",
    amount: "₦920,000",
    score: 86,
    band: "HIGH",
    action: "HOLD",
    signals: ["DEVICE_CHANGE", "VELOCITY_SPIKE"],
    time: "29 min ago",
    caseStatus: "OPEN",
  },
];

export default function Transactions() {
  const [search, setSearch] = useState("");
  const [bandFilter, setBandFilter] = useState("ALL");
  const [actionFilter, setActionFilter] = useState("ALL");

  const filteredTransactions = useMemo(() => {
    return transactions.filter((transaction) => {
      const matchesSearch =
        transaction.id.toLowerCase().includes(search.toLowerCase());

      const matchesBand =
        bandFilter === "ALL" || transaction.band === bandFilter;

      const matchesAction =
        actionFilter === "ALL" || transaction.action === actionFilter;

      return matchesSearch && matchesBand && matchesAction;
    });
  }, [search, bandFilter, actionFilter]);

  return (
    <div>
      <Sidebar />

      <main className="main-content">
        <div className="page-header">
          <div>
            <div className="eyebrow">RISK OPERATIONS</div>
            <h1>Payments</h1>
            <p>Review transactions evaluated by the TrustSentinel risk engine.</p>
          </div>

          <div className="status-pill">
            <span />
            SYNTHETIC DATA
          </div>
        </div>

        <section className="card transaction-toolbar">
          <div className="search-box">
            <Search size={16} />
            <input
              type="text"
              placeholder="Search transaction ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div className="filter-group">
            <SlidersHorizontal size={15} />

            <select
              value={bandFilter}
              onChange={(e) => setBandFilter(e.target.value)}
            >
              <option value="ALL">All Risk Bands</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="ELEVATED">Elevated</option>
              <option value="MODERATE">Moderate</option>
              <option value="LOW">Low</option>
            </select>

            <select
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
            >
              <option value="ALL">All Actions</option>
              <option value="HOLD">Hold</option>
              <option value="STEP-UP">Step-Up</option>
              <option value="WARN">Warn</option>
              <option value="ALLOW">Allow</option>
              <option value="REVIEW">Review</option>
            </select>
          </div>
        </section>

        <section className="card transaction-table-card">
          <div className="section-heading">
            <div>
              <h2>Transaction Queue</h2>
              <p>
                {filteredTransactions.length} transactions currently visible
              </p>
            </div>
          </div>

          <div className="table-wrap">
            <table className="transaction-table">
              <thead>
                <tr>
                  <th>Transaction</th>
                  <th>Amount</th>
                  <th>Score</th>
                  <th>Risk Band</th>
                  <th>Action</th>
                  <th>Signals</th>
                  <th>Time</th>
                  <th>Case</th>
                </tr>
              </thead>

              <tbody>
                {filteredTransactions.map((transaction) => (
                  <tr key={transaction.id}>
                    <td>
                      <Link
                        href={`/dashboard/transactions/${transaction.id}`}
                        className="transaction-link"
                      >
                        {transaction.id}
                      </Link>
                    </td>

                    <td>{transaction.amount}</td>

                    <td>
                      <strong>{transaction.score}</strong>
                    </td>

                    <td>
                      <span
                        className={`risk-badge risk-${transaction.band.toLowerCase()}`}
                      >
                        {transaction.band}
                      </span>
                    </td>

                    <td>
                      <span
                        className={`action-badge action-${transaction.action
                          .toLowerCase()
                          .replace("-", "")}`}
                      >
                        {transaction.action}
                      </span>
                    </td>

                    <td>
                      <div className="signal-count">
                        {transaction.signals.length} signals
                      </div>
                    </td>

                    <td>{transaction.time}</td>

                    <td>
                      <span
                        className={
                          transaction.caseStatus === "OPEN"
                            ? "case-open"
                            : "case-none"
                        }
                      >
                        {transaction.caseStatus}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {filteredTransactions.length === 0 && (
            <div className="table-empty">
              <strong>No transactions found</strong>
              <span>Try changing your search or filters.</span>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}