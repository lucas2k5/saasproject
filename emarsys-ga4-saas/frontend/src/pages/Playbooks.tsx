import DashboardLayout from "../components/DashboardLayout";

function Playbooks() {
  return (
    <DashboardLayout
      title="Playbooks"
      subtitle="Fluxos sugeridos para cada objetivo"
      label="Playbooks"
    >
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[
          { label: "Playbooks ativos", value: "14" },
          { label: "Em execucao", value: "6" },
          { label: "Automacoes", value: "22" },
          { label: "Personalizacoes", value: "38" }
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
              Playbooks sugeridos
            </h2>
            <p className="text-sm text-[color:var(--muted)]">
              Baseado no comportamento recente
            </p>
          </div>
          <div className="mt-6 grid gap-3">
            {["Recuperacao express", "Upsell de recorrencia", "Onboarding VIP"].map(
              (item) => (
                <div
                  className="flex items-center justify-between rounded-2xl border border-[color:var(--stroke)] bg-[color:var(--bg-soft)] px-4 py-3 text-sm"
                  key={item}
                >
                  <p className="text-[color:var(--ink)]">{item}</p>
                  <span className="text-xs uppercase tracking-[0.2em] text-[color:var(--muted)]">
                    Configurar
                  </span>
                </div>
              )
            )}
          </div>
        </article>
        <article className="rounded-3xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-6 shadow-[0_22px_40px_rgba(8,12,24,0.3)]">
          <div>
            <h2 className="text-lg font-semibold text-[color:var(--ink)]">
              Automacoes prontas
            </h2>
            <p className="text-sm text-[color:var(--muted)]">Templates em destaque</p>
          </div>
          <div className="mt-6 space-y-4">
            {["Cart Recovery", "Lead Nurture", "Reactivation"].map(
              (label, index) => (
                <div
                  className="grid grid-cols-[140px_1fr] items-center gap-4 text-sm"
                  key={label}
                >
                  <span className="text-[color:var(--muted)]">{label}</span>
                  <div className="h-2 rounded-full bg-[color:var(--stroke)]">
                    <div
                      className="h-2 rounded-full bg-gradient-to-r from-[color:var(--accent-2)] to-transparent"
                      style={{ width: `${82 - index * 12}%` }}
                    />
                  </div>
                </div>
              )
            )}
          </div>
        </article>
      </section>
    </DashboardLayout>
  );
}

export default Playbooks;
