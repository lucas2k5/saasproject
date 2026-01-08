import DashboardLayout from "../components/DashboardLayout";

function Analytics() {
  return (
    <DashboardLayout
      title="Analytics"
      subtitle="Visao 360o dos funis e comportamento"
      label="Analytics"
    >
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[
          { label: "Sessões", value: "482k" },
          { label: "Usuarios ativos", value: "118k" },
          { label: "Tempo medio", value: "4m 22s" },
          { label: "Engajamento", value: "62%" }
        ].map((item) => (
          <article
            className="rounded-2xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-5"
            key={item.label}
          >
            <p className="text-xs uppercase tracking-[0.25em] text-[color:var(--muted)]">
              {item.label}
            </p>
            <p className="mt-2 text-2xl font-semibold text-[color:var(--ink)]">
              {item.value}
            </p>
          </article>
        ))}
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.2fr_1fr]">
        <article className="rounded-3xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-6 shadow-[0_22px_40px_rgba(8,12,24,0.3)]">
          <div>
            <h2 className="text-lg font-semibold text-[color:var(--ink)]">
              Jornadas principais
            </h2>
            <p className="text-sm text-[color:var(--muted)]">Fluxos com maior conversao</p>
          </div>
          <div className="mt-6 space-y-4">
            {["Landing > Trial", "Cart > Checkout", "Email > Retorno", "Referral"].map(
              (label, index) => (
                <div
                  className="grid grid-cols-[150px_1fr] items-center gap-4 text-sm"
                  key={label}
                >
                  <span className="text-[color:var(--muted)]">{label}</span>
                  <div className="h-2 rounded-full bg-[color:var(--stroke)]">
                    <div
                      className="h-2 rounded-full bg-gradient-to-r from-[color:var(--accent-2)] to-transparent"
                      style={{ width: `${90 - index * 12}%` }}
                    />
                  </div>
                </div>
              )
            )}
          </div>
        </article>
        <article className="rounded-3xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-6 shadow-[0_22px_40px_rgba(8,12,24,0.3)]">
          <div>
            <h2 className="text-lg font-semibold text-[color:var(--ink)]">
              Alertas de comportamento
            </h2>
            <p className="text-sm text-[color:var(--muted)]">Variacoes detectadas hoje</p>
          </div>
          <div className="mt-6 grid gap-3">
            {["Queda no mobile", "Pico em paid", "Bounce alto em /pricing"].map(
              (item) => (
                <div
                  className="flex items-center justify-between rounded-2xl border border-[color:var(--stroke)] bg-[color:var(--bg-soft)] px-4 py-3 text-sm"
                  key={item}
                >
                  <p className="text-[color:var(--ink)]">{item}</p>
                  <span className="text-xs uppercase tracking-[0.2em] text-[color:var(--muted)]">
                    Monitorar
                  </span>
                </div>
              )
            )}
          </div>
        </article>
      </section>
    </DashboardLayout>
  );
}

export default Analytics;
