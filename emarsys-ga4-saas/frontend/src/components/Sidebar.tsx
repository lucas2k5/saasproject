import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useLocale } from "../context/LocaleContext";

const navItems = [
  { labelKey: "nav.overview", path: "/dashboard" },
  { labelKey: "nav.campaigns", path: "/dashboard/campaigns" },
  { labelKey: "nav.abandonedCarts", path: "/dashboard/abandoned-carts" },
  { labelKey: "nav.analytics", path: "/dashboard/analytics" },
  { labelKey: "nav.aiAdvisor", path: "/dashboard/ai-advisor" },
  { labelKey: "nav.playbooks", path: "/dashboard/playbooks" }
];

type SidebarProps = {
  theme: "dark" | "light";
  onToggleTheme: () => void;
};

function Sidebar({ theme, onToggleTheme }: SidebarProps) {
  const linkBase =
    "flex items-center gap-3 rounded-xl border border-transparent px-3 py-2 text-sm font-medium transition";
  const { user, signOut } = useAuth();
  const { t } = useLocale();
  const navigate = useNavigate();
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

  return (
    <aside className="flex w-full flex-col gap-8 border-b border-[color:var(--stroke)] bg-[color:var(--bg-soft)] px-6 py-6 backdrop-blur lg:min-h-screen lg:w-64 lg:border-b-0 lg:border-r">
      <div className="flex items-center gap-3">
        <span className="inline-flex h-10 w-10 items-center justify-center rounded-full border-2 border-[color:var(--accent)] shadow-[0_0_18px_rgba(255,122,61,0.35)]" />
        <div>
          <p className="text-sm font-semibold text-[color:var(--ink)]">KeepAIS</p>
        </div>
      </div>

      <nav className="space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.labelKey}
            to={item.path}
            className={({ isActive }) =>
              `${linkBase} ${
                isActive
                  ? "bg-[color:var(--surface-strong)] text-[color:var(--ink)]"
                  : "text-[color:var(--muted)] hover:bg-[color:var(--surface)] hover:text-[color:var(--ink)] hover:border-[color:var(--stroke)]"
              }`
            }
          >
            <span className="h-2.5 w-2.5 rounded-full bg-[color:var(--accent-2)] opacity-70" />
            {t(item.labelKey)}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto space-y-4">
        <button
          className="flex w-full items-center gap-3 rounded-2xl border border-[color:var(--stroke)] bg-[color:var(--surface)] px-4 py-3 text-xs font-semibold uppercase tracking-[0.2em] text-[color:var(--ink)]"
          type="button"
          onClick={onToggleTheme}
        >
          <span className="h-2.5 w-2.5 rounded-full bg-[color:var(--accent-2)]" />
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
