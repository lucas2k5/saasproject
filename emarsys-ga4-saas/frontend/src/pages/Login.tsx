import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useLocale } from "../context/LocaleContext";

function Login() {
  const { user, signIn, loading, error, hasSupabaseConfig } = useAuth();
  const { t } = useLocale();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const navigate = useNavigate();

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFormError(null);

    const result = await signIn(email, password);
    if (result) {
      setFormError(result);
      return;
    }

    navigate("/dashboard");
  };

  return (
    <div className="min-h-screen bg-[#0c0f1a] px-6 py-12 text-white">
      <div className="mx-auto grid w-full max-w-5xl gap-8 lg:grid-cols-[1.1fr_0.9fr]">
        <aside className="hidden flex-col justify-between rounded-3xl border border-white/10 bg-[radial-gradient(circle_at_top,_rgba(56,189,248,0.12),transparent_60%),radial-gradient(circle_at_bottom,_rgba(249,115,22,0.18),transparent_55%)] p-10 shadow-[0_30px_60px_rgba(7,11,24,0.45)] lg:flex">
          <div className="space-y-6">
            <div className="flex items-center">
              <img
                src="/brain-logo.png"
                alt="Logo em formato de cerebro"
                className="brand-brain-logo h-10 w-10 object-contain"
              />
            </div>
            <div className="space-y-3">
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-cyan-300">
                Workspace seguro
              </p>
              <h2 className="text-3xl font-semibold text-white">
                Centralize seus dados e decida com confiança.
              </h2>
              <p className="text-sm text-slate-300">
                Acompanhe métricas críticas de Emarsys, GA4 e CRM em um único painel.
              </p>
            </div>
          </div>
          <div className="space-y-3 text-sm text-slate-300">
            <p>• Dashboards em tempo real</p>
            <p>• Monitoramento de campanhas por canal</p>
            <p>• Insights acionáveis por IA</p>
          </div>
        </aside>

        <div className="flex w-full flex-col gap-6 rounded-3xl border border-white/10 bg-white/5 p-8 shadow-[0_30px_60px_rgba(7,11,24,0.45)]">
          <div className="space-y-2 text-center lg:text-left">
            <p className="text-xs font-semibold uppercase tracking-[0.35em] text-cyan-300 lg:hidden">
              Login
            </p>
            <h1 className="text-3xl font-semibold">{t("login.title")}</h1>
            <p className="text-sm text-slate-400">{t("login.subtitle")}</p>
          </div>

        {(formError || error) && (
          <div className="rounded-2xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            {formError || error}
          </div>
        )}

        <form className="space-y-4" onSubmit={handleSubmit}>
          <label className="flex flex-col gap-2 text-sm">
            {t("login.email")}
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm text-white outline-none focus:border-orange-400/70"
              placeholder="voce@empresa.com"
              required
              disabled={loading}
            />
          </label>
          <label className="flex flex-col gap-2 text-sm">
            {t("login.password")}
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm text-white outline-none focus:border-orange-400/70"
              placeholder="********"
              required
              disabled={loading}
            />
          </label>
          <button
            type="submit"
            disabled={loading || !hasSupabaseConfig}
            className="w-full rounded-full bg-orange-500 px-6 py-3 text-sm font-semibold text-slate-950 transition hover:bg-orange-400 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {loading ? t("login.loading") : t("login.submit")}
          </button>
        </form>

          <p className="text-center text-sm text-slate-400 lg:text-left">
            {t("login.signupPrompt")}{" "}
            <Link to="/signup" className="text-orange-300 hover:text-orange-200">
              {t("login.signupLink")}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;
