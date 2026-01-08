import DashboardLayout from "../components/DashboardLayout";

function Campaigns() {
  return (
    <DashboardLayout
      title="Campaigns"
      subtitle="Performance geral das campanhas ativas"
      label="Campaigns"
    >
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[
          { label: "Campanhas ativas", value: "28" },
          { label: "Envios hoje", value: "12.840" },
          { label: "CTR medio", value: "3.4%" },
          { label: "Conversoes", value: "1.294" }
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
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold text-[color:var(--ink)]">
                Top campanhas
              </h2>
              <p className="text-sm text-[color:var(--muted)]">
                Volume de conversoes por canal
              </p>
            </div>
            <div className="text-xs uppercase tracking-[0.2em] text-[color:var(--muted)]">
              Ultimos 7 dias
            </div>
          </div>
          <div className="mt-6 space-y-4">
            {["Email Pro", "Cart Rescue", "Winback", "Nurture"].map(
              (label, index) => (
                <div
                  className="grid grid-cols-[120px_1fr] items-center gap-4 text-sm"
                  key={label}
                >
                  <span className="text-[color:var(--muted)]">{label}</span>
                  <div className="h-2 rounded-full bg-[color:var(--stroke)]">
                    <div
                      className="h-2 rounded-full bg-gradient-to-r from-[color:var(--accent-2)] to-transparent"
                      style={{ width: `${88 - index * 14}%` }}
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
              Cadencias em teste
            </h2>
            <p className="text-sm text-[color:var(--muted)]">Experimentos ativos com IA</p>
          </div>
          <div className="mt-6 grid gap-3">
            {["CTA V2", "Assunto dinamico", "Timing 18h", "Segmento VIP"].map(
              (item) => (
                <div
                  className="flex items-center justify-between rounded-2xl border border-[color:var(--stroke)] bg-[color:var(--bg-soft)] px-4 py-3 text-sm"
                  key={item}
                >
                  <p className="text-[color:var(--ink)]">{item}</p>
                  <span className="text-xs uppercase tracking-[0.2em] text-[color:var(--muted)]">
                    Em andamento
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

export default Campaigns;
