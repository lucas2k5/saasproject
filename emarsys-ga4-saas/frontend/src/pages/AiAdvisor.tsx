import DashboardLayout from "../components/DashboardLayout";

function AiAdvisor() {
  return (
    <DashboardLayout
      title="AI Advisor"
      subtitle="Recomendacoes inteligentes para escalar resultados"
      label="AI Advisor"
    >
      <section className="panel chat-shell">
        <div className="chat-header">
          <div className="chat-title">
            <div className="chat-icon">✶</div>
            <div>
              <h2>KeepAIS Advisor</h2>
              <p>Powered by GPT-4</p>
            </div>
          </div>
          <div className="chat-actions">
            <button className="ghost-pill" type="button">
              Novo briefing
            </button>
            <button className="primary-pill" type="button">
              Gerar dashboard
            </button>
          </div>
        </div>

        <div className="chat-body">
          <div className="chat-message assistant">
            <div className="chat-avatar">AI</div>
            <div className="chat-bubble">
              <p>
                Ola! Sou seu KeepAIS Advisor. Descreva o objetivo do dashboard e
                quais metricas voce quer acompanhar.
              </p>
            </div>
          </div>
          <div className="chat-message user">
            <div className="chat-bubble">
              <p>
                Quero um dashboard de carrinho abandonado com conversoes por
                canal e taxa de recuperacao semanal.
              </p>
            </div>
            <div className="chat-avatar user">JD</div>
          </div>
          <div className="chat-message assistant">
            <div className="chat-avatar">AI</div>
            <div className="chat-bubble">
              <p>
                Perfeito. Vou montar um painel com: volume de carrinhos, valor
                recuperado, conversoes por canal e tendencia semanal. Quer
                incluir alertas automaticos?
              </p>
            </div>
          </div>
        </div>

        <form className="chat-input" onSubmit={(event) => event.preventDefault()}>
          <input
            type="text"
            placeholder="Peça um dashboard, pergunte sobre performance, ou descreva um playbook..."
          />
          <button className="send-button" type="submit">
            ➤
          </button>
        </form>
      </section>
    </DashboardLayout>
  );
}

export default AiAdvisor;
