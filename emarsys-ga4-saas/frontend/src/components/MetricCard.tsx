type MetricCardProps = {
  label: string;
  value: string;
  hint?: string;
};

function MetricCard({ label, value, hint }: MetricCardProps) {
  return (
    <article className="rounded-2xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-5">
      <p className="text-xs uppercase tracking-[0.25em] text-[color:var(--muted)]">
        {label}
      </p>
      <p className="mt-2 text-2xl font-semibold text-[color:var(--ink)]">{value}</p>
      {hint && <p className="mt-2 text-sm text-[color:var(--muted)]">{hint}</p>}
    </article>
  );
}

export default MetricCard;
