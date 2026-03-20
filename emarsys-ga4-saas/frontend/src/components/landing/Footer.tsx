import { Link } from "react-router-dom";

function Footer() {
  return (
    <footer className="border-t border-white/10 px-4 py-12 text-slate-400 sm:px-6 lg:px-8">
      <div className="mx-auto grid w-full max-w-6xl gap-10 md:grid-cols-[1.2fr_1fr_1fr_1fr]">
        <div className="grid gap-3">
          <div className="flex items-center gap-2.5">
            <span className="inline-flex h-9 w-9 items-center justify-center rounded-full border-2 border-orange-500 shadow-[0_0_18px_rgba(255,122,61,0.35)]" />
            <span className="text-sm font-semibold text-white">KeepAIS</span>
          </div>
          <p className="text-sm text-slate-400">
            Plataforma de inteligencia para times de marketing baseados em dados.
          </p>
        </div>

        <div className="grid gap-2 text-sm text-slate-400">
          <p className="font-semibold text-white">Produto</p>
          <a href="#features">Recursos</a>
          <a href="#product">Dashboards</a>
          <a href="#pricing">Planos</a>
        </div>

        <div className="grid gap-2 text-sm text-slate-400">
          <p className="font-semibold text-white">Empresa</p>
          <a href="#">Sobre</a>
          <a href="#">Carreiras</a>
          <a href="#">Contato</a>
        </div>

        <div className="grid gap-3 text-sm text-slate-400">
          <p className="font-semibold text-white">Console</p>
          <Link to="/dashboard" className="text-orange-300">
            Abrir dashboard
          </Link>
          <span>hello@keepais.com</span>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
