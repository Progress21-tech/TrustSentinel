import Link from "next/link";
import {
  Activity,
  BarChart3,
  BookOpen,
  BriefcaseBusiness,
  CreditCard,
  FileText,
  LayoutDashboard,
  Settings,
  ShieldCheck,
} from "lucide-react";

const navigation = [
  { label: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { label: "Payments", href: "/dashboard/transactions", icon: CreditCard },
  { label: "Simulator", href: "/dashboard/simulator", icon: Activity },
  { label: "Cases", href: "/dashboard/cases", icon: BriefcaseBusiness },
  { label: "Metrics", href: "/dashboard/metrics", icon: BarChart3 },
  { label: "Audit Log", href: "/dashboard/audit", icon: FileText },
  { label: "API Docs", href: "/dashboard/api-docs", icon: BookOpen },
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-icon">
          <ShieldCheck size={20} />
        </div>
        <div>
          <strong>TrustSentinel</strong>
          <span>Risk Operations</span>
        </div>
      </div>

      <nav>
        {navigation.map(({ label, href, icon: Icon }) => (
          <Link href={href} key={label} className="nav-item">
            <Icon size={18} />
            <span>{label}</span>
          </Link>
        ))}
      </nav>

      <div className="sidebar-bottom">
        <Link href="#" className="nav-item">
          <Settings size={18} />
          <span>Settings</span>
        </Link>
      </div>
    </aside>
  );
}