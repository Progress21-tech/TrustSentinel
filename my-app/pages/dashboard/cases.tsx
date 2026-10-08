import { useState } from "react";
import Link from "next/link";
import Sidebar from "../../components/layout/Sidebar";
import { Search, BriefcaseBusiness } from "lucide-react";

const cases = [
  {
    id: "case_00421",
    transaction: "txn_00841",
    band: "CRITICAL",
    action: "HOLD",
    status: "OPEN",
    outcome: "PENDING",
    analyst: "Unassigned",
    created: "2 min ago",
    updated: "2 min ago",
  },
  {
    id: "case_00420",
    transaction: "txn_00840",
    band: "ELEVATED",
    action: "STEP-UP",
    status: "OPEN",
    outcome: "PENDING",
    analyst: "A. Analyst",
    created: "8 min ago",
    updated: "6 min ago",
  },
  {
    id: "case_00419",
    transaction: "txn_00837",
    band: "HIGH",
    action: "HOLD",
    status: "OPEN",
    outcome: "PENDING",
    analyst: "Unassigned",
    created: "29 min ago",
    updated: "29 min ago",
  },
  {
    id: "case_00418",
    transaction: "txn_00832",
    band: "CRITICAL",
    action: "REVIEW",
    status: "CLOSED",
    outcome: "CONFIRMED_SCAM",
    analyst: "J. Analyst",
    created: "1 hr ago",
    updated: "42 min ago",
  },
];

export default function Cases() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("ALL");

  const filteredCases = cases.filter((item) => {
    const matchesSearch =
      item.id.toLowerCase().includes(search.toLowerCase()) ||
      item.transaction.toLowerCase().includes(search.toLowerCase());

    const matchesStatus = status === "ALL" || item.status === status;

    return matchesSearch && matchesStatus;
  });

  return (
    <div>
      <Sidebar />

      <main className="main-content">
        <div className="page-header">
          <div>
            <div className="eyebrow">RISK OPERATIONS</div>
            <h1>Cases</h1>
            <p>Investigate and resolve transactions requiring analyst attention.</p>
          </div>

          <div className="status-pill">
            <span />
            SYNTHETIC DATA
          </div>
        </div>

        <section className="card cases-toolbar">
          <div className="search-box">
            <Search size={16} />
            <input
              placeholder="Search case or transaction..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <select
            className="case-filter"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <option value="ALL">All Statuses</option>
            <option value="OPEN">Open</option>
            <option value="CLOSED">Closed</option>
          </select>
        </section>

        <section className="card cases-table-card">
          <div className="section-heading">
            <div>
              <h2>Investigation Queue</h2>
              <p>{filteredCases.length} cases currently visible</p>
            </div>
          </div>

          <div className="table-wrap">
            <table className="cases-table">
              <thead>
                <tr>
                  <th>Case ID</th>
                  <th>Transaction</th>
                  <th>Risk Band</th>
                  <th>Action</th>
                  <th>Status</th>
                  <th>Outcome</th>
                  <th>Analyst</th>
                  <th>Created</th>
                  <th>Updated</th>
                </tr>
              </thead>

              <tbody>
                {filteredCases.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <Link
                        href={`/dashboard/cases/${item.id}`}
                        className="case-link"
                      >
                        {item.id}
                      </Link>
                    </td>

                    <td>{item.transaction}</td>

                    <td>
                      <span
                        className={`risk-badge risk-${item.band.toLowerCase()}`}
                      >
                        {item.band}
                      </span>
                    </td>

                    <td>
                      <span
                        className={`action-badge action-${item.action
                          .toLowerCase()
                          .replace("-", "")}`}
                      >
                        {item.action}
                      </span>
                    </td>

                    <td>
                      <span
                        className={
                          item.status === "OPEN"
                            ? "case-status-open"
                            : "case-status-closed"
                        }
                      >
                        {item.status}
                      </span>
                    </td>

                    <td>
                      <span className="outcome-text">{item.outcome}</span>
                    </td>

                    <td>{item.analyst}</td>
                    <td>{item.created}</td>
                    <td>{item.updated}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {filteredCases.length === 0 && (
            <div className="table-empty">
              <BriefcaseBusiness size={28} />
              <strong>No cases found</strong>
              <span>Try changing your search or filter.</span>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}