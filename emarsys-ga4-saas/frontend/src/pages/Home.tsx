import { useEffect } from "react";
import { Link } from "react-router-dom";

function Home() {
  useEffect(() => {
    const elements = document.querySelectorAll("[data-animate]");

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("in-view");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.2 }
    );

    elements.forEach((element) => observer.observe(element));

    return () => observer.disconnect();
  }, []);

  return (
    <div className="landing">
      <header className="landing-nav">
        <div className="logo">
          <span className="logo-mark">◎</span>
          <span>KipiAIs</span>
        </div>
        <nav className="landing-links">
          <a href="#features">Recursos</a>
          <a href="#modules">Modulos</a>
          <a href="#plans">Planos</a>
          <a href="#integrations">Integracoes</a>
        </nav>
        <div className="landing-actions">
          <button className="ghost-pill" type="button">
            Entrar
          </button>
          <Link className="primary-pill" to="/dashboard">
            Abrir Console
          </Link>
        </div>
      </header>

      <section className="hero-grid" data-animate>
        <div>
          <p className="eyebrow">B2B Marketing Intelligence</p>
          <h1 className="hero-title">
            KipiAIs: o SaaS que transforma dados de marketing em insights e planos de ação.
          </h1>
          <p className="hero-subtitle">
            Construa jornadas, monitore conversoes e antecipe o abandono de carrinho
            com uma camada unica de analytics e automacao.
          </p>
          <div className="hero-actions">
            <Link className="primary-pill" to="/dashboard">
              Ver dashboard
            </Link>
            <button className="ghost-pill" type="button">
              Ver demo
            </button>
          </div>
          <div className="hero-metrics">
            <div>
              <p className="metric-value">+42%</p>
              <p className="metric-label">Taxa de abertura</p>
            </div>
            <div>
              <p className="metric-value">-18%</p>
              <p className="metric-label">Churn de campanha</p>
            </div>
            <div>
              <p className="metric-value">7x</p>
              <p className="metric-label">Velocidade de insight</p>
            </div>
          </div>
        </div>
        <div className="hero-panel" data-animate>
          <div className="hero-panel-header">
            <p>Live Control Room</p>
            <span>Emarsys + GA4</span>
          </div>
          <div className="hero-panel-body">
            <div className="pulse-card">
              <p>Campanhas em execucao</p>
              <h3>128</h3>
              <span className="pulse">+12 hoje</span>
            </div>
            <div className="pulse-card">
              <p>Conversoes por hora</p>
              <h3>3.842</h3>
              <span className="pulse">+7.1%</span>
            </div>
            <div className="wave-chart">
              <span />
              <span />
              <span />
              <span />
              <span />
            </div>
          </div>
        </div>
      </section>

      <section id="features" className="landing-section" data-animate>
        <div className="section-head">
          <h2>Visao futurista do seu marketing</h2>
          <p>
            Tudo o que o time precisa para monitorar campanhas, jornadas e
            conversoes sem alternar entre plataformas.
          </p>
        </div>
        <div className="feature-grid stagger" data-animate>
          {[
            {
              title: "Signals Engine",
              text: "Unifica eventos de carrinho, campanhas e GA4 em tempo real."
            },
            {
              title: "Playbooks inteligentes",
              text: "Sugestoes de acoes baseadas em comportamento e intenção."
            },
            {
              title: "Dashboards modulados",
              text: "Crie visoes personalizaveis por equipe e objetivo."
            }
          ].map((item) => (
            <article className="feature-card" key={item.title}>
              <div className="feature-icon">◆</div>
              <h3>{item.title}</h3>
              <p>{item.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="modules" className="landing-section modules" data-animate>
        <div className="section-head">
          <h2>Back-office para orquestrar o seu SaaS</h2>
          <p>
            Navegue por modulos especificos e personalize indicadores para cada
            squad.
          </p>
        </div>
        <div className="module-grid stagger" data-animate>
          {[
            "Overview",
            "Campaigns",
            "Abandoned Carts",
            "Analytics",
            "AI Advisor",
            "Playbooks"
          ].map((label) => (
            <div className="module-card" key={label}>
              <p>{label}</p>
              <span>Configurar</span>
            </div>
          ))}
        </div>
      </section>

      <section id="plans" className="landing-section plans" data-animate>
        <div className="section-head">
          <h2>Planos que evoluem com a sua operacao</h2>
          <p>Escolha o nivel de inteligencia e automacao que o seu time precisa.</p>
        </div>
        <div className="plans-grid stagger" data-animate>
          {[
            {
              title: "Starter",
              price: "R$ 1.490",
              desc: "Dashboards essenciais e monitoramento basico."
            },
            {
              title: "Growth",
              price: "R$ 3.900",
              desc: "Alertas inteligentes + playbooks personalizaveis."
            },
            {
              title: "Enterprise",
              price: "Sob consulta",
              desc: "IA dedicada, SLA premium e squads ilimitados."
            }
          ].map((plan) => (
            <article className="plan-card" key={plan.title}>
              <h3>{plan.title}</h3>
              <p className="plan-price">{plan.price}</p>
              <p className="plan-desc">{plan.desc}</p>
              <button className="primary-pill" type="button">
                Escolher plano
              </button>
            </article>
          ))}
        </div>
      </section>

      <section id="integrations" className="landing-section integrations" data-animate>
        <div className="section-head">
          <h2>Integracoes nativas</h2>
          <p>Feito para plugar rapido nas suas fontes principais.</p>
        </div>
        <div className="integration-row stagger" data-animate>
          {["Emarsys", "GA4", "CRM", "CDP", "Ads"].map((label) => (
            <div className="integration-pill" key={label}>
              {label}
            </div>
          ))}
        </div>
      </section>

      <section className="cta-banner" data-animate>
        <div>
          <h2>Pronto para acelerar a performance?</h2>
          <p>Ative o console e veja o que esta acontecendo agora.</p>
        </div>
        <Link className="primary-pill" to="/dashboard">
          Abrir Dashboard
        </Link>
      </section>
    </div>
  );
}

export default Home;
