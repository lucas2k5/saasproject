type TrendPoint = {
  date: string;
  value: number;
};

type TrendChartProps = {
  title: string;
  points: TrendPoint[];
};

function TrendChart({ title, points }: TrendChartProps) {
  const maxValue = Math.max(...points.map((point) => point.value), 1);
  const chartWidth = 700;
  const chartHeight = 200;
  const paddingX = 28;
  const barGap = 16;
  const barWidth =
    (chartWidth - paddingX * 2 - barGap * (points.length - 1)) /
    Math.max(points.length, 1);

  return (
    <section className="rounded-3xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-6 shadow-[0_22px_40px_rgba(8,12,24,0.3)]">
      <header className="flex items-start justify-between gap-4">
        <h2 className="text-lg font-semibold text-[color:var(--ink)]">{title}</h2>
        <p className="text-xs uppercase tracking-[0.2em] text-[color:var(--muted)]">
          Ultimos 7 dias
        </p>
      </header>
      <div className="mt-4 rounded-2xl border border-[color:var(--stroke)] bg-[color:var(--bg-soft)] p-4">
        <svg
          viewBox={`0 0 ${chartWidth} 240`}
          role="img"
          aria-label={title}
          className="text-[color:var(--muted)]"
        >
          <defs>
            <linearGradient id="barFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#ff7a59" />
              <stop offset="100%" stopColor="#f2b26b" />
            </linearGradient>
          </defs>
          {points.map((point, index) => {
            const x = index * (barWidth + barGap) + paddingX;
            const height = Math.round((point.value / maxValue) * chartHeight);
            const y = 200 - height;

            return (
              <g key={point.date}>
                <rect
                  x={x}
                  y={y}
                  width={barWidth}
                  height={height}
                  rx={12}
                  fill="url(#barFill)"
                />
                <text x={x + barWidth / 2} y={224} textAnchor="middle">
                  {point.date.slice(5)}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </section>
  );
}

export default TrendChart;
