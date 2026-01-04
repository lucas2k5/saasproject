import DashboardLayout from "../components/DashboardLayout";

function AbandonedCarts() {
  return (
    <DashboardLayout
      title="Abandoned Carts"
      subtitle="Recuperacao de carrinhos em tempo real"
      label="Abandoned Carts"
    >
      <section className="stats-grid">
        {[
          { label: "Carrinhos abertos", value: "1.842" },
          { label: "Recuperados", value: "612" },
          { label: "Valor recuperado", value: "R$ 84k" },
          { label: "Fluxos ativos", value: "9" }
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
              <h2>Fluxos com maior impacto</h2>
              <p>Automacoes mais eficientes</p>
            </div>
          </div>
          <div className="panel-bars">
            {["Resgate 3 passos", "Push + Email", "Remarketing", "Fallback"].map(
              (label, index) => (
                <div className="bar-row" key={label}>
                  <span>{label}</span>
                  <div className="bar-track">
                    <div
                      className="bar-fill"
                      style={{ width: `${86 - index * 10}%` }}
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
              <h2>Insights recomendados</h2>
              <p>Oportunidades detectadas pela IA</p>
            </div>
          </div>
          <div className="list-grid">
            {["Ajustar timing mobile", "Cupom para high intent", "Retargeting express"].map(
              (item) => (
                <div className="list-card" key={item}>
                  <p>{item}</p>
                  <span>Prioridade alta</span>
                </div>
              )
            )}
          </div>
        </article>
      </section>
    </DashboardLayout>
  );
}

export default AbandonedCarts;
