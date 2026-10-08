import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import Link from "next/link";
import {
  Activity, BarChart3, BookOpen, ClipboardList, FileText, LayoutDashboard,
  LogOut, ShieldCheck, Waypoints,
} from "lucide-react";
import { clearSession, getHealth, getReady } from "@/lib/api";

const navigation = [
  { label: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { label: "Transactions", href: "/dashboard/transactions", icon: Waypoints },
  { label: "Score transaction", href: "/dashboard/score", icon: ShieldCheck },
  { label: "Cases", href: "/dashboard/cases", icon: ClipboardList },
  { label: "Sandbox", href: "/dashboard/simulator", icon: Activity },
  { label: "Metrics", href: "/dashboard/metrics", icon: BarChart3 },
  { label: "Audit trail", href: "/dashboard/audit", icon: FileText },
  { label: "API reference", href: "/dashboard/api-docs", icon: BookOpen },
];

export default function Sidebar() {
  const router = useRouter();
  const [apiStatus, setApiStatus] = useState("Checking");
  const [mlStatus, setMlStatus] = useState("Checking");

  useEffect(() => {
    let active = true;
    async function refresh() {
      const [health, ready] = await Promise.allSettled([getHealth(), getReady()] as const);
      if (!active) return;
      setApiStatus(health.status === "fulfilled" && health.value.status === "ok" ? "Operational" : "Unavailable");
      setMlStatus(ready.status === "fulfilled" ? ready.value.ml_status.replaceAll("_", " ") : "Unavailable");
    }
    void refresh();
    const interval = window.setInterval(refresh, 60000);
    return () => { active = false; window.clearInterval(interval); };
  }, []);

  function logout() {
    clearSession();
    window.dispatchEvent(new Event("trustsentinel:logout"));
    void router.replace("/login");
  }

  return (
    <aside className="sidebar">
      <Link href="/dashboard" className="brand-lockup sidebar-brand">
        <span className="brand-mark"><ShieldCheck size={21} /></span>
        <span><strong>TrustSentinel</strong><small>INNOVATEX · RISK INTELLIGENCE</small></span>
      </Link>
      <div className="nav-caption">WORKSPACE</div>
      <nav aria-label="Main navigation">
        {navigation.map(({ label, href, icon: Icon }) => {
          const selected = href === "/dashboard" ? router.pathname === href : router.pathname.startsWith(href);
          return <Link href={href} key={href} aria-current={selected ? "page" : undefined} className={`nav-item${selected ? " active" : ""}`}>
            <Icon size={17} strokeWidth={1.8} /><span>{label}</span>
          </Link>;
        })}
      </nav>
      <div className="sidebar-spacer" />
      <div className="system-status" aria-label="Live system status">
        <div className="nav-caption">SYSTEM STATUS</div>
        <div className="system-row"><span className={`status-dot ${apiStatus === "Operational" ? "online" : ""}`} />API <b>{apiStatus}</b></div>
        <div className="system-row"><span className={`status-dot ${mlStatus === "available" ? "online" : ""}`} />ML engine <b>{mlStatus}</b></div>
      </div>
      <div className="analyst-profile"><div className="profile-avatar">RA</div><div><strong>Risk Analyst</strong><small>Analyst workspace</small></div><button type="button" className="icon-button logout-button" onClick={logout} aria-label="Sign out" title="Sign out"><LogOut size={17} /></button></div>
    </aside>
  );
}
