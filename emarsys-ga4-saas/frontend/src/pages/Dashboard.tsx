import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import AreaChart from "../components/AreaChart";
import DashboardLayout from "../components/DashboardLayout";
import StatCard from "../components/StatCard";
import { useAuth } from "../context/AuthContext";
import { useLocale } from "../context/LocaleContext";
import { fetchReport, type ReportSource } from "../lib/api";
import { fetchEngagementPrediction } from "../lib/ml";
import type { ReportPayload } from "../types/reports";

const formatter = new Intl.NumberFormat("pt-BR");
const currencyFormatter = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  maximumFractionDigits: 0
});
const percentFormatter = new Intl.NumberFormat("pt-BR", {
  style: "percent",
  maximumFractionDigits: 1
});

const sources: { id: ReportSource; labelKey: string }[] = [
  { id: "combined", labelKey: "source.combined" },
  { id: "emarsys", labelKey: "source.emarsys" },
  { id: "ga4", labelKey: "source.ga4" }
];

const mockReport: ReportPayload = {
  source: "combined",
  summary: {
    sends: 42800,
    opens: 17650,
    clicks: 4680,
    conversions: 1020,
    openRate: 0.41,
    clickRate: 0.11,
    conversionRate: 0.024
  },
  series: [
    { date: "2024-10-01", sends: 5800, opens: 2300, clicks: 580, conversions: 120 },
    { date: "2024-10-02", sends: 6100, opens: 2580, clicks: 620, conversions: 140 },
    { date: "2024-10-03", sends: 5900, opens: 2400, clicks: 610, conversions: 130 },
    { date: "2024-10-04", sends: 6300, opens: 2620, clicks: 680, conversions: 150 },
    { date: "2024-10-05", sends: 6150, opens: 2500, clicks: 640, conversions: 155 },
    { date: "2024-10-06", sends: 6100, opens: 2570, clicks: 720, conversions: 170 },
    { date: "2024-10-07", sends: 5450, opens: 2680, clicks: 810, conversions: 155 }
  ],
  updatedAt: "2024-10-07T12:00:00Z",
  sources: {
    emarsysUpdatedAt: "2024-10-07T12:00:00Z",
    ga4UpdatedAt: "2024-10-07T12:00:00Z"
  }
};

const channelMix = [
  { labelKey: "channel.email", value: 42, color: "#35d5ff" },
  { labelKey: "channel.sms", value: 18, color: "#ffb86b" },
  { labelKey: "channel.push", value: 14, color: "#8b7bff" },
  { labelKey: "channel.ads", value: 26, color: "#ff6a3d" }
];

const funnelSteps = [
  { labelKey: "funnel.sends", key: "sends" },
  { labelKey: "funnel.opens", key: "opens" },
  { labelKey: "funnel.clicks", key: "clicks" },
  { labelKey: "funnel.conversions", key: "conversions" }
];

const createConicGradient = (items: { value: number; color: string }[]) => {
  const total = items.reduce((sum, item) => sum + item.value, 0) || 1;
  let current = 0;
  const stops = items.map((item) => {
    const start = current;
    const size = (item.value / total) * 100;
    const end = start + size;
    current = end;
    return `${item.color} ${start}% ${end}%`;
  });
  return stops.join(", ");
};

const clamp = (value: number, min: number, max: number) =>
  Math.min(max, Math.max(min, value));

function Dashboard() {
  const [source, setSource] = useState<ReportSource>("combined");
  const { user } = useAuth();
  const { t } = useLocale();

  const { data, isLoading, error } = useQuery({
    queryKey: ["reports", source],
    queryFn: () => fetchReport(source)
  });

  const report = data as ReportPayload | undefined;
  const resolvedReport = report ?? mockReport;
  const usingMock = !report || !!error;
  const summary = resolvedReport.summary;
  const series = resolvedReport.series ?? [];
  const sourceLabel =
    sources.find((item) => item.id === source)?.labelKey ?? "source.combined";
  const chartPoints = useMemo(
    () =>
      series.map((point) => ({ date: point.date, value: point.conversions })),
    [series]
  );
  const channelGradient = useMemo(() => createConicGradient(channelMix), []);
  const plotPoints = useMemo(
    () =>
      series.map((point) => ({
        x: clamp(point.opens / Math.max(point.sends, 1), 0, 1),
        y: clamp(point.clicks / Math.max(point.opens, 1), 0, 1)
      })),
    [series]
  );
  const plotTrend = useMemo(() => {
    if (!plotPoints.length) {
      return { slope: 0, intercept: 0.5 };
    }
    const meanX = plotPoints.reduce((sum, point) => sum + point.x, 0) / plotPoints.length;
    const meanY = plotPoints.reduce((sum, point) => sum + point.y, 0) / plotPoints.length;
    const numerator = plotPoints.reduce(
      (sum, point) => sum + (point.x - meanX) * (point.y - meanY),
      0
    );
    const denominator = plotPoints.reduce(
      (sum, point) => sum + (point.x - meanX) * (point.x - meanX),
      0
    );
    const slope = denominator === 0 ? 0 : numerator / denominator;
    const intercept = meanY - slope * meanX;
    return { slope, intercept };
  }, [plotPoints]);

  const openRate = summary.openRate ?? 0;
  const conversionRate = summary.conversionRate ?? 0;
  const revenue = (summary.conversions ?? 0) * 120;
  const abandonedValue = (summary.clicks ?? 0) * 42;
  const mlFeatures = useMemo(
    () => ({
      source,
      sends: summary?.sends ?? 0,
      opens: summary?.opens ?? 0,
      clicks: summary?.clicks ?? 0,
      conversions: summary?.conversions ?? 0,
      openRate: summary?.openRate ?? 0,
      conversionRate: summary?.conversionRate ?? 0
    }),
    [source, summary]
  );

  const {
    data: prediction,
    isLoading: isMlLoading,
    error: mlError
  } = useQuery({
    queryKey: ["ml", "engagement", user?.id, source],
    queryFn: () => fetchEngagementPrediction(user?.id ?? "demo", mlFeatures),
    enabled: !!summary
  });

  const scoreLabel = prediction ? percentFormatter.format(prediction.score) : "--";
  const segmentLabel = prediction
    ? t(`segment.${prediction.segment}`)
    : "--";
  const mlDelta = mlError
    ? t("dashboard.unavailable")
    : isMlLoading
      ? t("dashboard.loading")
      : `${t("dashboard.segment")}: ${segmentLabel}`;
  const mlVariant =
    mlError ? "negative" : prediction?.segment === "high" ? "positive" : "neutral";

  return (
    <DashboardLayout
      title={t("dashboard.title")}
      subtitle={t("dashboard.subtitle")}
      label={t("dashboard.label")}
    >
      <section className="flex flex-wrap items-center gap-3 rounded-2xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-3">
        {sources.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`rounded-full border px-4 py-2 text-xs font-semibold uppercase tracking-[0.25em] transition ${
              source === item.id
                ? "border-transparent bg-[color:var(--surface-strong)] text-[color:var(--ink)]"
                : "border-[color:var(--stroke)] text-[color:var(--muted)] hover:text-[color:var(--ink)]"
            }`}
            onClick={() => setSource(item.id)}
          >
            {t(item.labelKey)}
          </button>
        ))}
        <span className="ml-auto text-sm text-[color:var(--muted)]">
          {t("dashboard.activeSource")}: {t(sourceLabel)}
        </span>
        {usingMock && (
          <span className="rounded-full border border-[color:var(--stroke)] px-3 py-1 text-xs uppercase tracking-[0.2em] text-[color:var(--muted)]">
            {t("dashboard.mockData")}
          </span>
        )}
      </section>

      {isLoading && !report && (
        <div className="rounded-2xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-6 text-sm text-[color:var(--muted)]">
          {t("dashboard.loading")}
        </div>
      )}

      {summary && (
        <>
          <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            <StatCard
              label={t("dashboard.stat.totalRevenue")}
              value={currencyFormatter.format(revenue)}
              delta="+12.5%"
              variant="positive"
              icon="$"
            />
            <StatCard
              label={t("dashboard.stat.abandonedValue")}
              value={currencyFormatter.format(abandonedValue)}
              delta="-4.2%"
              variant="negative"
              icon="🛒"
            />
            <StatCard
              label={t("dashboard.stat.openRate")}
              value={percentFormatter.format(openRate)}
              delta="+2.1%"
              variant="positive"
              icon="✉️"
            />
            <StatCard
              label={t("dashboard.stat.recoveryRate")}
              value={percentFormatter.format(conversionRate)}
              delta="+5.4%"
              variant="positive"
              icon="⟳"
            />
            <StatCard
              label={t("dashboard.stat.engagementScore")}
              value={scoreLabel}
              delta={mlDelta}
              variant={mlVariant}
              icon="✨"
            />
          </section>

          <section className="grid gap-4 xl:grid-cols-[1.4fr_1fr]">
            <AreaChart
              title={t("dashboard.panel.performanceTitle")}
              subtitle={t("dashboard.panel.performanceSubtitle")}
              series={chartPoints}
              tags={[t("dashboard.panel.last7Days"), t("dashboard.panel.live")]}
            />
            <section className="rounded-3xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-6 shadow-[0_22px_40px_rgba(8,12,24,0.3)]">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold text-[color:var(--ink)]">
                    {t("dashboard.panel.bounceTitle")}
                  </h2>
                  <p className="text-sm text-[color:var(--muted)]">
                    {t("dashboard.panel.bounceSubtitle")}
                  </p>
                </div>
                <div className="text-xs uppercase tracking-[0.2em] text-[color:var(--muted)]">
                  12 {t("dashboard.panel.campaignsLabel")}
                </div>
              </div>
              <div className="mt-6 space-y-4">
                {["Alpha", "Nova", "Pulse", "Orbit"].map((label, index) => (
                  <div
                    className="grid grid-cols-[90px_1fr] items-center gap-4 text-sm"
                    key={label}
                  >
                    <span className="text-[color:var(--muted)]">{label}</span>
                    <div className="h-2 rounded-full bg-[color:var(--stroke)]">
                      <div
                        className="h-2 rounded-full bg-gradient-to-r from-[color:var(--accent-2)] to-transparent"
                        style={{ width: `${80 - index * 12}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </section>

          <section className="grid gap-4 xl:grid-cols-3">
            <section className="rounded-3xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-6 shadow-[0_22px_40px_rgba(8,12,24,0.3)]">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold text-[color:var(--ink)]">
                    {t("dashboard.panel.mixTitle")}
                  </h2>
                  <p className="text-sm text-[color:var(--muted)]">
                    {t("dashboard.panel.mixSubtitle")}
                  </p>
                </div>
              </div>
              <div className="mt-6 flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
                <div className="relative h-36 w-36 sm:h-44 sm:w-44">
                  <div
                    className="h-full w-full rounded-full"
                    style={{ background: `conic-gradient(${channelGradient})` }}
                  />
                  <div className="absolute inset-7 rounded-full bg-[color:var(--surface)]" />
                  <div className="absolute inset-0 flex items-center justify-center text-sm font-semibold text-[color:var(--ink)]">
                    100%
                  </div>
                </div>
                <div className="grid gap-3 text-sm">
                  {channelMix.map((item) => (
                    <div className="flex items-center gap-3" key={item.labelKey}>
                      <span
                        className="h-3 w-3 rounded-full"
                        style={{ backgroundColor: item.color }}
                      />
                      <span className="text-[color:var(--muted)]">
                        {t(item.labelKey)}
                      </span>
                      <span className="ml-auto font-semibold text-[color:var(--ink)]">
                        {item.value}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className="rounded-3xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-6 shadow-[0_22px_40px_rgba(8,12,24,0.3)]">
              <div>
                <h2 className="text-lg font-semibold text-[color:var(--ink)]">
                  {t("dashboard.panel.plotTitle")}
                </h2>
                <p className="text-sm text-[color:var(--muted)]">
                  {t("dashboard.panel.plotSubtitle")}
                </p>
              </div>
              <div className="mt-6 rounded-2xl border border-[color:var(--stroke)] bg-[color:var(--bg-soft)] p-4">
                <svg
                  viewBox="0 0 320 200"
                  role="img"
                  aria-label="Plot de engajamento"
                  className="h-52 w-full"
                  preserveAspectRatio="xMidYMid meet"
                >
                  {(() => {
                    const margin = { left: 40, right: 16, top: 24, bottom: 28 };
                    const width = 320 - margin.left - margin.right;
                    const height = 200 - margin.top - margin.bottom;
                    const yBase = margin.top + height;
                    const xBase = margin.left;
                    const trendY0 = clamp(plotTrend.intercept, 0, 1);
                    const trendY1 = clamp(plotTrend.slope + plotTrend.intercept, 0, 1);

                    return (
                      <>
                        {[0.25, 0.5, 0.75].map((line) => (
                          <line
                            key={line}
                            x1={xBase}
                            x2={xBase + width}
                            y1={yBase - line * height}
                            y2={yBase - line * height}
                            stroke="var(--stroke)"
                          />
                        ))}
                        {[0.25, 0.5, 0.75].map((line) => (
                          <line
                            key={`x-${line}`}
                            y1={margin.top}
                            y2={yBase}
                            x1={xBase + line * width}
                            x2={xBase + line * width}
                            stroke="var(--stroke)"
                          />
                        ))}
                        <line
                          x1={xBase}
                          y1={yBase}
                          x2={xBase + width}
                          y2={yBase}
                          stroke="var(--muted)"
                          strokeWidth={1.2}
                        />
                        <line
                          x1={xBase}
                          y1={margin.top}
                          x2={xBase}
                          y2={yBase}
                          stroke="var(--muted)"
                          strokeWidth={1.2}
                        />
                        <line
                          x1={xBase}
                          y1={yBase - trendY0 * height}
                          x2={xBase + width}
                          y2={yBase - trendY1 * height}
                          stroke="var(--ink)"
                          strokeWidth={2}
                        />
                        {plotPoints.map((point, index) => {
                          const x = xBase + point.x * width;
                          const y = yBase - point.y * height;
                          return (
                            <circle
                              key={index}
                              cx={x}
                              cy={y}
                              r={4.5}
                              fill="var(--accent-2)"
                              fillOpacity={0.9}
                            />
                          );
                        })}
                        {[0, 0.5, 1].map((tick) => (
                          <text
                            key={`x-label-${tick}`}
                            x={xBase + tick * width}
                            y={yBase + 18}
                            textAnchor="middle"
                            fontSize="10"
                            fill="var(--muted)"
                          >
                            {Math.round(tick * 100)}%
                          </text>
                        ))}
                        {[0, 0.5, 1].map((tick) => (
                          <text
                            key={`y-label-${tick}`}
                            x={xBase - 8}
                            y={yBase - tick * height}
                            textAnchor="end"
                            fontSize="10"
                            fill="var(--muted)"
                            dominantBaseline="middle"
                          >
                            {Math.round(tick * 100)}%
                          </text>
                        ))}
                        <text
                          x={xBase + width / 2}
                          y={200}
                          textAnchor="middle"
                          fontSize="11"
                          fill="var(--muted)"
                        >
                          {t("dashboard.panel.plotXAxis")}
                        </text>
                        <text
                          x={10}
                          y={margin.top + height / 2}
                          textAnchor="middle"
                          fontSize="11"
                          fill="var(--muted)"
                          transform={`rotate(-90 10 ${margin.top + height / 2})`}
                        >
                          {t("dashboard.panel.plotYAxis")}
                        </text>
                        <g>
                          <circle cx={xBase} cy={margin.top - 10} r={4} fill="var(--accent-2)" />
                          <text
                            x={xBase + 12}
                            y={margin.top - 6}
                            fontSize="11"
                            fill="var(--muted)"
                          >
                            {t("dashboard.panel.plotLegend")}
                          </text>
                        </g>
                      </>
                    );
                  })()}
                </svg>
              </div>
            </section>

            <section className="rounded-3xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-6 shadow-[0_22px_40px_rgba(8,12,24,0.3)]">
              <div>
                <h2 className="text-lg font-semibold text-[color:var(--ink)]">
                  {t("dashboard.panel.funnelTitle")}
                </h2>
                <p className="text-sm text-[color:var(--muted)]">
                  {t("dashboard.panel.funnelSubtitle")}
                </p>
              </div>
              <div className="mt-6 space-y-4">
                {funnelSteps.map((step) => {
                  const value = summary[step.key as keyof typeof summary] as number;
                  const width = summary.sends ? (value / summary.sends) * 100 : 0;
                  return (
                    <div className="space-y-2 text-sm" key={step.labelKey}>
                      <div className="flex items-center justify-between text-[color:var(--muted)]">
                        <span>{t(step.labelKey)}</span>
                        <span className="text-[color:var(--ink)]">
                          {formatter.format(value)}
                        </span>
                      </div>
                      <div className="h-2 rounded-full bg-[color:var(--stroke)]">
                        <div
                          className="h-2 rounded-full bg-gradient-to-r from-[color:var(--accent)] to-transparent"
                          style={{ width: `${Math.max(width, 8)}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          </section>

        </>
      )}
    </DashboardLayout>
  );
}

export default Dashboard;
