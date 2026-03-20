import { useState } from "react";
import { Link, NavLink, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useLocale } from "../context/LocaleContext";
import {
  LayoutDashboard,
  TrendingUp,
  Megaphone,
  ShoppingCart,
  BarChart3,
  BrainCircuit,
  BookOpen,
  Plug,
  Eye,
  Globe,
  Upload,
  Users,
  ClipboardList,
  Percent,
  Settings,
  ChevronDown,
} from "lucide-react";

/* ── Main nav items ── */
const navItems = [
  { labelKey: "nav.overview", path: "/dashboard", end: true, icon: LayoutDashboard },
  { labelKey: "nav.recommendations", path: "/dashboard/recommendations", icon: TrendingUp },
  { labelKey: "nav.campaigns", path: "/dashboard/campaigns", icon: Megaphone },
  { labelKey: "nav.abandonedCarts", path: "/dashboard/abandoned-carts", icon: ShoppingCart },
  { labelKey: "nav.analytics", path: "/dashboard/analytics", icon: BarChart3 },
  { labelKey: "nav.aiAdvisor", path: "/dashboard/ai-advisor", icon: BrainCircuit },
  { labelKey: "nav.playbooks", path: "/dashboard/playbooks", icon: BookOpen },
  { labelKey: "nav.integrations", path: "/dashboard/integrations", icon: Plug },
];

/* ── Recommendation sub-items grouped by section ── */
const recSections = [
  {
    title: "PRINCIPAL",
    items: [
      { label: "Visão Geral", path: "/dashboard/recommendations", end: true, icon: LayoutDashboard },
      { label: "Ciclo de Vida", path: "/dashboard/recommendations/lifecycle", icon: TrendingUp },
      { label: "Cargas", path: "/dashboard/recommendations/uploads", icon: Upload },
    ],
  },
  {
    title: "DADOS",
    items: [
      { label: "Clientes", path: "/dashboard/recommendations/customers", icon: Users },
      { label: "Pedidos", path: "/dashboard/recommendations/orders", icon: ClipboardList },
      { label: "Ofertas", path: "/dashboard/recommendations/offers", icon: Percent },
    ],
  },
  {
    title: "SIMULADOR & IA",
    items: [
      { label: "Catálogo", path: "/dashboard/recommendations/catalog", icon: Globe },
      { label: "Configurações", path: "/dashboard/recommendations/config", icon: Settings },
    ],
  },
];

type SidebarProps = {
  theme: "dark" | "light";
  onToggleTheme: () => void;
};

function Sidebar({ theme, onToggleTheme }: SidebarProps) {
  const linkBase =
    "flex items-center gap-3 rounded-xl border border-transparent px-3 py-2 text-sm font-medium transition";
  const subLinkBase =
    "flex items-center gap-2.5 rounded-lg px-3 py-1.5 text-[13px] font-medium transition";
  const { user, signOut } = useAuth();
  const { t } = useLocale();
  const navigate = useNavigate();
  const location = useLocation();
  const metadata = user?.user_metadata as Record<string, unknown> | undefined;
  const fullName = typeof metadata?.full_name === "string" ? metadata.full_name : null;
  const companyName =
    typeof metadata?.company_name === "string" ? metadata.company_name : null;
  const email = user?.email ?? null;
  const displayName = fullName || email || "Usuário";
  const displayCompany = companyName || "Workspace";
  const initials = displayName
    .split(" ")
    .map((part) => part[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();

  const isRecActive = location.pathname.startsWith("/dashboard/recommendations");
  const [recOpen, setRecOpen] = useState(isRecActive);

  return (
    <aside className="flex w-full flex-col gap-6 border-b border-[color:var(--stroke)] bg-[color:var(--bg-soft)] px-5 py-6 backdrop-blur lg:min-h-screen lg:w-64 lg:border-b-0 lg:border-r">
      <div className="flex items-center gap-3">
        <span className="inline-flex h-10 w-10 items-center justify-center rounded-full border-2 border-[color:var(--accent)] shadow-[0_0_18px_rgba(255,122,61,0.35)]" />
        <p className="text-sm font-semibold text-[color:var(--ink)]">KeepAIS</p>
      </div>

      <nav className="space-y-1">
        {navItems.map((item) => {
          const isRec = item.labelKey === "nav.recommendations";
          const Icon = item.icon;

          if (isRec) {
            return (
              <div key={item.labelKey}>
                <button
                  type="button"
                  onClick={() => {
                    setRecOpen((prev) => !prev);
                    if (!isRecActive) {
                      navigate("/dashboard/recommendations");
                    }
                  }}
                  className={`${linkBase} w-full ${
                    isRecActive
                      ? "bg-[color:var(--surface-strong)] text-[color:var(--ink)]"
                      : "text-[color:var(--muted)] hover:bg-[color:var(--surface)] hover:text-[color:var(--ink)] hover:border-[color:var(--stroke)]"
                  }`}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  <span className="flex-1 text-left">{t(item.labelKey)}</span>
                  <ChevronDown
                    className={`h-3.5 w-3.5 shrink-0 transition-transform duration-200 ${recOpen ? "rotate-180" : ""}`}
                  />
                </button>

                {/* Dropdown with sections */}
                <div
                  className={`overflow-hidden transition-all duration-200 ${
                    recOpen ? "max-h-[600px] opacity-100 mt-1" : "max-h-0 opacity-0"
                  }`}
                >
                  <div className="ml-2 border-l border-[color:var(--stroke)] pl-3 py-1 space-y-3">
                    {recSections.map((section) => (
                      <div key={section.title}>
                        <p className="px-3 pb-1 text-[10px] font-bold uppercase tracking-[0.15em] text-[color:var(--muted)] opacity-70">
                          {section.title}
                        </p>
                        <div className="space-y-0.5">
                          {section.items.map((sub) => {
                            const SubIcon = sub.icon;
                            return (
                              <NavLink
                                key={sub.path}
                                to={sub.path}
                                end={sub.end}
                                className={({ isActive }) =>
                                  `${subLinkBase} ${
                                    isActive
                                      ? "bg-[color:var(--surface-strong)] text-[color:var(--ink)]"
                                      : "text-[color:var(--muted)] hover:text-[color:var(--ink)] hover:bg-[color:var(--surface)]"
                                  }`
                                }
                              >
                                <SubIcon className="h-3.5 w-3.5 shrink-0" />
                                {sub.label}
                              </NavLink>
                            );
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            );
          }

          return (
            <NavLink
              key={item.labelKey}
              to={item.path}
              end={item.end}
              className={({ isActive }) =>
                `${linkBase} ${
                  isActive
                    ? "bg-[color:var(--surface-strong)] text-[color:var(--ink)]"
                    : "text-[color:var(--muted)] hover:bg-[color:var(--surface)] hover:text-[color:var(--ink)] hover:border-[color:var(--stroke)]"
                }`
              }
            >
              <Icon className="h-4 w-4 shrink-0" />
              {t(item.labelKey)}
            </NavLink>
          );
        })}
      </nav>

      <div className="mt-auto space-y-4">
        <button
          className="flex w-full items-center gap-3 rounded-2xl border border-[color:var(--stroke)] bg-[color:var(--surface)] px-4 py-3 text-xs font-semibold uppercase tracking-[0.2em] text-[color:var(--ink)]"
          type="button"
          onClick={onToggleTheme}
        >
          <Eye className="h-4 w-4 shrink-0" />
          <span className="flex-1 text-left">
            {theme === "dark" ? t("sidebar.darkMode") : t("sidebar.lightMode")}
          </span>
          <span className="rounded-full bg-[color:var(--surface-strong)] px-3 py-1 text-[10px] font-semibold text-[color:var(--muted)]">
            {theme === "dark" ? t("sidebar.on") : t("sidebar.off")}
          </span>
        </button>

        <div className="rounded-2xl border border-[color:var(--stroke)] bg-[color:var(--surface)] px-4 py-4">
          <Link
            to="/dashboard/profile"
            className="flex items-start gap-3 transition hover:opacity-90"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[rgba(255,106,61,0.2)] text-sm font-semibold text-[color:var(--accent)]">
              {initials}
            </div>
            <div className="min-w-0">
              <p className="text-[11px] uppercase tracking-[0.3em] text-[color:var(--muted)]">
                {t("sidebar.workspace")}
              </p>
              <p className="truncate text-sm font-semibold text-[color:var(--ink)]">
                {displayName}
              </p>
              <p className="truncate text-xs text-[color:var(--muted)]">
                {displayCompany}
              </p>
              {email && (
                <p className="truncate text-xs text-[color:var(--muted)]">{email}</p>
              )}
            </div>
          </Link>
          <button
            className="mt-4 inline-flex w-full items-center justify-center rounded-2xl border border-[color:var(--stroke)] px-4 py-2.5 text-xs font-semibold uppercase tracking-[0.18em] text-[color:var(--ink)] opacity-80 transition hover:opacity-100 sm:w-auto"
            type="button"
            onClick={async () => {
              const result = await signOut();
              if (!result) {
                navigate("/login");
              }
            }}
          >
            {t("sidebar.logout")}
          </button>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
