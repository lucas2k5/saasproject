import { NavLink } from "react-router-dom";

const navItems = [
  { label: "Overview", path: "/dashboard" },
  { label: "Campaigns", path: "/dashboard/campaigns" },
  { label: "Abandoned Carts", path: "/dashboard/abandoned-carts" },
  { label: "Analytics", path: "/dashboard/analytics" },
  { label: "AI Advisor", path: "/dashboard/ai-advisor" },
  { label: "Playbooks", path: "/dashboard/playbooks" }
];

type SidebarProps = {
  theme: "dark" | "light";
  onToggleTheme: () => void;
};

function Sidebar({ theme, onToggleTheme }: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="brand-mark">◎</span>
        <div>
          <p className="brand-title">KipiAIs</p>
          <p className="brand-subtitle">Emarsys + GA4</p>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <NavLink key={item.label} to={item.path} className="sidebar-link">
            <span className="dot" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <button className="toggle" type="button" onClick={onToggleTheme}>
          <span className="dot" />
          {theme === "dark" ? "Dark Mode" : "Light Mode"}
          <span className="toggle-pill">{theme === "dark" ? "On" : "Off"}</span>
        </button>
        <div className="user-card">
          <div className="avatar">JD</div>
          <div>
            <p className="user-name">John Doe</p>
            <p className="user-role">Admin Workspace</p>
          </div>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
