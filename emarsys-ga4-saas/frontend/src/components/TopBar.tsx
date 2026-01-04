type TopBarProps = {
  title: string;
  subtitle: string;
  label?: string;
};

function TopBar({ title, subtitle, label = "Dashboard Overview" }: TopBarProps) {
  return (
    <header className="topbar">
      <div>
        <p className="topbar-label">{label}</p>
        <h1>{title}</h1>
        <p className="topbar-subtitle">{subtitle}</p>
      </div>
      <div className="topbar-actions">
        <button className="ghost-pill" type="button">
          Preview
        </button>
        <button className="primary-pill" type="button">
          Sync Data Source
        </button>
      </div>
    </header>
  );
}

export default TopBar;
