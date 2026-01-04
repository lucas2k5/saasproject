type ChartPoint = {
  date: string;
  value: number;
};

type AreaChartProps = {
  title: string;
  subtitle: string;
  series: ChartPoint[];
  accent?: string;
};

function AreaChart({ title, subtitle, series, accent = "#ff7a59" }: AreaChartProps) {
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
    <section className="panel">
      <div className="panel-header">
        <div>
          <h2>{title}</h2>
          <p>{subtitle}</p>
        </div>
        <div className="panel-tags">
          <span>Last 7 days</span>
          <span>Live</span>
        </div>
      </div>
      <div className="panel-chart">
        <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={title}>
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
