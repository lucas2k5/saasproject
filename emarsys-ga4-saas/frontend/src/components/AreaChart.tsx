type ChartPoint = {
  date: string;
  value: number;
};

type AreaChartProps = {
  title: string;
  subtitle: string;
  series: ChartPoint[];
  accent?: string;
  tags?: string[];
};

function AreaChart({
  title,
  subtitle,
  series,
  accent = "var(--accent)",
  tags = []
}: AreaChartProps) {
  const maxValue = Math.max(...series.map((point) => point.value), 1);
  const width = 680;
  const height = 240;
  const padding = 32;

  const points = series.map((point, index) => {
    const x = padding + (index / Math.max(series.length - 1, 1)) * (width - padding * 2);
    const y = height - padding - (point.value / maxValue) * (height - padding * 2);
    return { x, y };
  });

  const linePath = points
    .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`)
    .join(" ");

  const areaPath = `${linePath} L ${width - padding} ${height - padding} L ${padding} ${height - padding} Z`;

  return (
    <section className="rounded-3xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-6 shadow-[0_22px_40px_rgba(8,12,24,0.3)]">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-[color:var(--ink)]">{title}</h2>
          <p className="text-sm text-[color:var(--muted)]">{subtitle}</p>
        </div>
        {tags.length > 0 && (
          <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-[color:var(--muted)]">
            {tags.map((tag) => (
              <span key={tag}>{tag}</span>
            ))}
          </div>
        )}
      </div>
      <div className="mt-6 rounded-2xl border border-[color:var(--stroke)] bg-[color:var(--bg-soft)] p-4">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          role="img"
          aria-label={title}
          className="h-56 w-full"
          preserveAspectRatio="xMidYMid meet"
        >
          <defs>
            <linearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={accent} stopOpacity="0.35" />
              <stop offset="100%" stopColor={accent} stopOpacity="0" />
            </linearGradient>
          </defs>
          <path d={areaPath} fill="url(#areaFill)" />
          <path d={linePath} fill="none" stroke={accent} strokeWidth="3" />
          {points.map((point, index) => (
            <circle key={index} cx={point.x} cy={point.y} r="4" fill={accent} />
          ))}
        </svg>
      </div>
    </section>
  );
}

export default AreaChart;
