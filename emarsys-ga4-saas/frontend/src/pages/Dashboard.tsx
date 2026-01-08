import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import AreaChart from "../components/AreaChart";
import DashboardLayout from "../components/DashboardLayout";
import StatCard from "../components/StatCard";
import { useAuth } from "../context/AuthContext";
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

const sources: { id: ReportSource; label: string }[] = [
  { id: "combined", label: "Combinado" },
  { id: "emarsys", label: "Emarsys" },
  { id: "ga4", label: "GA4" }
];

const segmentLabels: Record<string, string> = {
  high: "Alto",
  medium: "Médio",
  low: "Baixo"
};

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
  { label: "Email", value: 42, color: "#35d5ff" },
  { label: "SMS", value: 18, color: "#ffb86b" },
  { label: "Push", value: 14, color: "#8b7bff" },
  { label: "Ads", value: 26, color: "#ff6a3d" }
];

const funnelSteps = [
  { label: "Envios", key: "sends" },
  { label: "Aberturas", key: "opens" },
  { label: "Cliques", key: "clicks" },
  { label: "Conversões", key: "conversions" }
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

function Dashboard() {
  const [source, setSource] = useState<ReportSource>("combined");
  const { user } = useAuth();

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
    sources.find((item) => item.id === source)?.label ?? "Combinado";
  const chartPoints = useMemo(
    () =>
      series.map((point) => ({ date: point.date, value: point.conversions })),
    [series]
  );
  const channelGradient = useMemo(() => createConicGradient(channelMix), []);
  const plotPoints = useMemo(
    () =>
      series.map((point) => ({
        x: point.opens / Math.max(point.sends, 1),
        y: point.clicks / Math.max(point.opens, 1)
      })),
    [series]
  );

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
    ? segmentLabels[prediction.segment] ?? prediction.segment
    : "--";
  const mlDelta = mlError ? "Indisponível" : isMlLoading ? "Carregando" : `Segmento: ${segmentLabel}`;
  const mlVariant =
    mlError ? "negative" : prediction?.segment === "high" ? "positive" : "neutral";

  return (
    <DashboardLayout
      title="Dashboard Overview"
      subtitle="Unified Emarsys & Google Analytics insights"
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
            {item.label}
          </button>
        ))}
        <span className="ml-auto text-sm text-[color:var(--muted)]">
          Fonte ativa: {sourceLabel}
        </span>
        {usingMock && (
          <span className="rounded-full border border-[color:var(--stroke)] px-3 py-1 text-xs uppercase tracking-[0.2em] text-[color:var(--muted)]">
            Dados simulados
          </span>
        )}
      </section>

      {isLoading && !report && (
        <div className="rounded-2xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-6 text-sm text-[color:var(--muted)]">
          Carregando dados...
        </div>
      )}

      {summary && (
        <>
          <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            <StatCard
              label="Total Revenue"
              value={currencyFormatter.format(revenue)}
              delta="+12.5%"
              variant="positive"
              icon="$"
            />
            <StatCard
              label="Abandoned Cart Value"
              value={currencyFormatter.format(abandonedValue)}
              delta="-4.2%"
              variant="negative"
              icon="🛒"
            />
            <StatCard
              label="Avg. Open Rate"
              value={percentFormatter.format(openRate)}
              delta="+2.1%"
              variant="positive"
              icon="✉️"
            />
            <StatCard
              label="Cart Recovery Rate"
              value={percentFormatter.format(conversionRate)}
              delta="+5.4%"
              variant="positive"
              icon="⟳"
            />
            <StatCard
              label="Engagement Score"
              value={scoreLabel}
              delta={mlDelta}
              variant={mlVariant}
              icon="✨"
            />
          </section>

          <section className="grid gap-4 xl:grid-cols-[1.4fr_1fr]">
            <AreaChart
              title="Campaign Performance & Abandoned Carts"
              subtitle="Evolucao de conversoes no periodo"
              series={chartPoints}
            />
            <section className="rounded-3xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-6 shadow-[0_22px_40px_rgba(8,12,24,0.3)]">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold text-[color:var(--ink)]">
                    Bounce Rates by Campaign
                  </h2>
                  <p className="text-sm text-[color:var(--muted)]">
                    Benchmark dos ultimos disparos
                  </p>
                </div>
                <div className="text-xs uppercase tracking-[0.2em] text-[color:var(--muted)]">
                  12 campaigns
                </div>
              </div>
              <div className="mt-6 space-y-4">
                {["Alpha", "Nova", "Pulse", "Orbit"].map((label, index) => (
                  <div className="grid grid-cols-[90px_1fr] items-center gap-4 text-sm" key={label}>
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
                    Mix de canais
                  </h2>
                  <p className="text-sm text-[color:var(--muted)]">
                    Distribuicao percentual de origem
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
                    <div className="flex items-center gap-3" key={item.label}>
                      <span
                        className="h-3 w-3 rounded-full"
                        style={{ backgroundColor: item.color }}
                      />
                      <span className="text-[color:var(--muted)]">{item.label}</span>
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
                  Plot de engajamento
                </h2>
                <p className="text-sm text-[color:var(--muted)]">
                  Relacao entre abertura e clique
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
                  {[0.25, 0.5, 0.75].map((line) => (
                    <line
                      key={line}
                      x1={24}
                      x2={296}
                      y1={200 - 24 - line * 152}
                      y2={200 - 24 - line * 152}
                      stroke="rgba(255,255,255,0.08)"
                    />
                  ))}
                  {[0.25, 0.5, 0.75].map((line) => (
                    <line
                      key={`x-${line}`}
                      y1={24}
                      y2={176}
                      x1={24 + line * 272}
                      x2={24 + line * 272}
                      stroke="rgba(255,255,255,0.08)"
                    />
                  ))}
                  <line x1={24} y1={176} x2={296} y2={176} stroke="rgba(255,255,255,0.2)" />
                  <line x1={24} y1={24} x2={24} y2={176} stroke="rgba(255,255,255,0.2)" />
                  {plotPoints.map((point, index) => {
                    const x = 24 + point.x * 272;
                    const y = 176 - point.y * 152;
                    return (
                      <circle key={index} cx={x} cy={y} r={5} fill="var(--accent)" />
                    );
                  })}
                </svg>
              </div>
            </section>

            <section className="rounded-3xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-6 shadow-[0_22px_40px_rgba(8,12,24,0.3)]">
              <div>
                <h2 className="text-lg font-semibold text-[color:var(--ink)]">
                  Funil de conversao
                </h2>
                <p className="text-sm text-[color:var(--muted)]">
                  Evolucao dos usuarios pelo funil
                </p>
              </div>
              <div className="mt-6 space-y-4">
                {funnelSteps.map((step) => {
                  const value = summary[step.key as keyof typeof summary] as number;
                  const width = summary.sends ? (value / summary.sends) * 100 : 0;
                  return (
                    <div className="space-y-2 text-sm" key={step.label}>
                      <div className="flex items-center justify-between text-[color:var(--muted)]">
                        <span>{step.label}</span>
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
