type TopBarProps = {
  title: string;
  subtitle: string;
  label?: string;
};

function TopBar({ title, subtitle, label = "Dashboard Overview" }: TopBarProps) {
  return (
    <header className="flex flex-col gap-6 border-b border-[color:var(--stroke)] pb-6 lg:flex-row lg:items-center lg:justify-between">
      <div className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[color:var(--muted)]">
          {label}
        </p>
        <h1 className="text-3xl font-semibold text-[color:var(--ink)] font-display">
          {title}
        </h1>
        <p className="text-sm text-[color:var(--muted)]">{subtitle}</p>
      </div>
      <div className="flex flex-wrap gap-3">
        <button
          className="rounded-full border border-[color:var(--stroke)] px-5 py-2.5 text-sm font-semibold text-[color:var(--ink)] opacity-80 transition hover:opacity-100"
          type="button"
        >
          Preview
        </button>
        <button
          className="rounded-full bg-[color:var(--accent)] px-5 py-2.5 text-sm font-semibold text-slate-950 shadow-[0_12px_30px_rgba(255,106,61,0.35)] transition hover:bg-[#ff8a66]"
          type="button"
        >
          Sync Data Source
        </button>
      </div>
    </header>
  );
}

export default TopBar;
