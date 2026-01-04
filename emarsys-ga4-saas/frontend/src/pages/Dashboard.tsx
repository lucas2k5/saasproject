import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import AreaChart from "../components/AreaChart";
import DashboardLayout from "../components/DashboardLayout";
import StatCard from "../components/StatCard";
import { fetchReport, type ReportSource } from "../lib/api";
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

function Dashboard() {
  const [source, setSource] = useState<ReportSource>("combined");

  const { data, isLoading, error } = useQuery({
    queryKey: ["reports", source],
    queryFn: () => fetchReport(source)
  });

  const report = data as ReportPayload | undefined;
  const summary = report?.summary;
  const series = report?.series ?? [];
  const sourceLabel =
    sources.find((item) => item.id === source)?.label ?? "Combinado";
  const chartPoints = useMemo(
    () =>
      series.map((point) => ({ date: point.date, value: point.conversions })),
    [series]
  );

  const openRate = summary?.openRate ?? 0;
  const conversionRate = summary?.conversionRate ?? 0;
  const revenue = (summary?.conversions ?? 0) * 120;
  const abandonedValue = (summary?.clicks ?? 0) * 42;

  return (
    <DashboardLayout
      title="Dashboard Overview"
      subtitle="Unified Emarsys & Google Analytics insights"
    >
      <section className="segment-control">
        {sources.map((item) => (
          <button
            key={item.id}
            type="button"
            className={source === item.id ? "segment active" : "segment"}
            onClick={() => setSource(item.id)}
          >
            {item.label}
          </button>
        ))}
        <span className="segment-meta">Fonte ativa: {sourceLabel}</span>
      </section>

      {isLoading && <div className="panel loading">Carregando dados...</div>}
      {(error || !report) && (
        <div className="panel loading error">
          Nao foi possivel carregar o dashboard. Tente novamente.
        </div>
      )}

      {report && summary && (
        <>
          <section className="stats-grid">
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
          </section>

          <section className="panels-grid">
            <AreaChart
              title="Campaign Performance & Abandoned Carts"
              subtitle="Evolucao de conversoes no periodo"
              series={chartPoints}
            />
            <section className="panel">
              <div className="panel-header">
                <div>
                  <h2>Bounce Rates by Campaign</h2>
                  <p>Benchmark dos ultimos disparos</p>
                </div>
                <div className="panel-tags">
                  <span>12 campaigns</span>
                </div>
              </div>
              <div className="panel-bars">
                {["Alpha", "Nova", "Pulse", "Orbit"].map((label, index) => (
                  <div className="bar-row" key={label}>
                    <span>{label}</span>
                    <div className="bar-track">
                      <div
                        className="bar-fill"
                        style={{ width: `${80 - index * 12}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </section>
        </>
      )}
    </DashboardLayout>
  );
}

export default Dashboard;
