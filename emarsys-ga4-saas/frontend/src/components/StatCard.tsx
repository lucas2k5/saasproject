type StatCardProps = {
  label: string;
  value: string;
  delta: string;
  variant?: "positive" | "negative" | "neutral";
  icon: string;
};

function StatCard({ label, value, delta, variant = "neutral", icon }: StatCardProps) {
  const deltaStyles = {
    positive: "bg-[color:var(--positive-bg)] text-[color:var(--positive-text)]",
    negative: "bg-[color:var(--negative-bg)] text-[color:var(--negative-text)]",
    neutral: "bg-[color:var(--neutral-bg)] text-[color:var(--neutral-text)]"
  } as const;

  return (
    <article className="relative grid gap-4 rounded-2xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-5 shadow-[0_18px_36px_rgba(8,12,24,0.25)] transition hover:-translate-y-1 hover:shadow-[0_22px_40px_rgba(8,12,24,0.35)]">
      <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-[color:var(--stroke)] bg-[color:var(--bg-soft)] text-[color:var(--accent-2)]">
        {icon}
      </div>
      <div>
        <p className="text-xs uppercase tracking-[0.25em] text-[color:var(--muted)]">
          {label}
        </p>
        <p className="text-2xl font-semibold text-[color:var(--ink)]">{value}</p>
      </div>
      <span
        className={`absolute right-4 top-4 rounded-full px-3 py-1 text-xs font-semibold ${deltaStyles[variant]}`}
      >
        {delta}
      </span>
    </article>
  );
}

export default StatCard;
