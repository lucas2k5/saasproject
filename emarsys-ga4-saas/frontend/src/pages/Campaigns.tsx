import DashboardLayout from "../components/DashboardLayout";

function Campaigns() {
  return (
    <DashboardLayout
      title="Campaigns"
      subtitle="Performance geral das campanhas ativas"
      label="Campaigns"
    >
      <section className="stats-grid">
        {[
          { label: "Campanhas ativas", value: "28" },
          { label: "Envios hoje", value: "12.840" },
          { label: "CTR medio", value: "3.4%" },
          { label: "Conversoes", value: "1.294" }
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
              <h2>Top campanhas</h2>
              <p>Volume de conversoes por canal</p>
            </div>
            <div className="panel-tags">
              <span>Ultimos 7 dias</span>
            </div>
          </div>
          <div className="panel-bars">
            {["Email Pro", "Cart Rescue", "Winback", "Nurture"].map(
              (label, index) => (
                <div className="bar-row" key={label}>
                  <span>{label}</span>
                  <div className="bar-track">
                    <div
                      className="bar-fill"
                      style={{ width: `${88 - index * 14}%` }}
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
              <h2>Cadencias em teste</h2>
              <p>Experimentos ativos com IA</p>
            </div>
          </div>
          <div className="list-grid">
            {["CTA V2", "Assunto dinamico", "Timing 18h", "Segmento VIP"].map(
              (item) => (
                <div className="list-card" key={item}>
                  <p>{item}</p>
                  <span>Em andamento</span>
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
