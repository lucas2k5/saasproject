import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import GoogleIcon from "../components/GoogleIcon";
import { useAuth } from "../context/AuthContext";

function Login() {
  const { user, signIn, signInWithGoogle, loading, error, hasSupabaseConfig } = useAuth();
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
    <div className="min-h-screen bg-[#0c0f1a] px-6 py-16 text-white">
      <div className="mx-auto flex w-full max-w-md flex-col gap-6 rounded-3xl border border-white/10 bg-white/5 p-8 shadow-[0_30px_60px_rgba(7,11,24,0.45)]">
        <div className="space-y-2 text-center">
          <h1 className="text-3xl font-semibold">Entrar no KeepAIS</h1>
          <p className="text-sm text-slate-400">
            Use seu e-mail corporativo para acessar o dashboard.
          </p>
        </div>

        {(formError || error) && (
          <div className="rounded-2xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            {formError || error}
          </div>
        )}

        <button
          type="button"
          onClick={async () => {
            setFormError(null);
            const result = await signInWithGoogle();
            if (result) {
              setFormError(result);
            }
          }}
          disabled={loading || !hasSupabaseConfig}
          className="flex w-full items-center justify-center gap-3 rounded-full border border-white/10 bg-white/5 px-6 py-3 text-sm font-semibold text-white transition hover:border-white/20 disabled:cursor-not-allowed disabled:opacity-70"
        >
          <GoogleIcon className="h-5 w-5" />
          Continuar com Google
        </button>

        <div className="flex items-center gap-3 text-xs uppercase tracking-[0.2em] text-slate-500">
          <span className="h-px flex-1 bg-white/10" />
          ou
          <span className="h-px flex-1 bg-white/10" />
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          <label className="flex flex-col gap-2 text-sm">
            E-mail
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
            Senha
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
            {loading ? "Entrando..." : "Entrar"}
          </button>
        </form>

        <p className="text-center text-sm text-slate-400">
          Ainda não tem conta?{" "}
          <Link to="/signup" className="text-orange-300 hover:text-orange-200">
            Criar conta
          </Link>
        </p>
      </div>
    </div>
  );
}

export default Login;
