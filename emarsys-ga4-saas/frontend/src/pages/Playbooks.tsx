import DashboardLayout from "../components/DashboardLayout";

function Playbooks() {
  return (
    <DashboardLayout
      title="Playbooks"
      subtitle="Fluxos sugeridos para cada objetivo"
      label="Playbooks"
    >
      <section className="stats-grid">
        {[
          { label: "Playbooks ativos", value: "14" },
          { label: "Em execucao", value: "6" },
          { label: "Automacoes", value: "22" },
          { label: "Personalizacoes", value: "38" }
        ].map((item) => (
          <article className="panel" key={item.label}>
            <p className="stat-label">{item.label}</p>
            <p className="stat-value">{item.value}</p>
          </article>
        ))}
      </section>

      <section className="panels-grid">
        <article className="panel">
          <div className="panel-header">
            <div>
              <h2>Playbooks sugeridos</h2>
              <p>Baseado no comportamento recente</p>
            </div>
          </div>
          <div className="list-grid">
            {["Recuperacao express", "Upsell de recorrencia", "Onboarding VIP"].map(
              (item) => (
                <div className="list-card" key={item}>
                  <p>{item}</p>
                  <span>Configurar</span>
                </div>
              )
            )}
          </div>
        </article>
        <article className="panel">
          <div className="panel-header">
            <div>
              <h2>Automacoes prontas</h2>
              <p>Templates em destaque</p>
            </div>
          </div>
          <div className="panel-bars">
            {["Cart Recovery", "Lead Nurture", "Reactivation"].map(
              (label, index) => (
                <div className="bar-row" key={label}>
                  <span>{label}</span>
                  <div className="bar-track">
                    <div
                      className="bar-fill"
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
