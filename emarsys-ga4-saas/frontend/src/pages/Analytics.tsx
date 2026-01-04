import DashboardLayout from "../components/DashboardLayout";

function Analytics() {
  return (
    <DashboardLayout
      title="Analytics"
      subtitle="Visao 360o dos funis e comportamento"
      label="Analytics"
    >
      <section className="stats-grid">
        {[
          { label: "Sessões", value: "482k" },
          { label: "Usuarios ativos", value: "118k" },
          { label: "Tempo medio", value: "4m 22s" },
          { label: "Engajamento", value: "62%" }
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
              <h2>Jornadas principais</h2>
              <p>Fluxos com maior conversao</p>
            </div>
          </div>
          <div className="panel-bars">
            {["Landing > Trial", "Cart > Checkout", "Email > Retorno", "Referral"].map(
              (label, index) => (
                <div className="bar-row" key={label}>
                  <span>{label}</span>
                  <div className="bar-track">
                    <div
                      className="bar-fill"
                      style={{ width: `${90 - index * 12}%` }}
                    />
                  </div>
                </div>
              )
            )}
          </div>
        </article>
        <article className="panel">
          <div className="panel-header">
            <div>
              <h2>Alertas de comportamento</h2>
              <p>Variacoes detectadas hoje</p>
            </div>
          </div>
          <div className="list-grid">
            {["Queda no mobile", "Pico em paid", "Bounce alto em /pricing"].map(
              (item) => (
                <div className="list-card" key={item}>
                  <p>{item}</p>
                  <span>Monitorar</span>
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
