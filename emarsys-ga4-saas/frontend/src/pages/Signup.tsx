import { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import GoogleIcon from "../components/GoogleIcon";
import { useAuth } from "../context/AuthContext";
import { useLocale } from "../context/LocaleContext";

function Signup() {
  const { user, signUp, signInWithGoogle, loading, error, hasSupabaseConfig } = useAuth();
  const { t } = useLocale();
  const [fullName, setFullName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [marketingConsent, setMarketingConsent] = useState<"opt-in" | "opt-out" | "">("");
  const [formError, setFormError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFormError(null);
    setSuccessMessage(null);

    if (!marketingConsent) {
      setFormError(t("signup.consentError"));
      return;
    }

    const result = await signUp({
      fullName,
      email,
      password,
      phone,
      companyName,
      marketingOptIn: marketingConsent === "opt-in"
    });
    if (result) {
      setFormError(result);
      return;
    }

    setSuccessMessage(t("signup.success"));
  };

  return (
    <div className="min-h-screen bg-[#0c0f1a] px-6 py-16 text-white">
      <div className="mx-auto flex w-full max-w-md flex-col gap-6 rounded-3xl border border-white/10 bg-white/5 p-8 shadow-[0_30px_60px_rgba(7,11,24,0.45)]">
        <Link
          to="/login"
          className="self-start text-xs font-semibold uppercase tracking-[0.2em] text-slate-400 transition hover:text-white"
        >
          {t("signup.back")}
        </Link>
        <div className="space-y-2 text-center">
          <h1 className="text-3xl font-semibold">{t("signup.title")}</h1>
          <p className="text-sm text-slate-400">{t("signup.subtitle")}</p>
        </div>

        {(formError || error) && (
          <div className="rounded-2xl border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            {formError || error}
          </div>
        )}

        {successMessage && (
          <div className="rounded-2xl border border-emerald-500/40 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
            {successMessage}
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
          {t("signup.google")}
        </button>

        <div className="flex items-center gap-3 text-xs uppercase tracking-[0.2em] text-slate-500">
          <span className="h-px flex-1 bg-white/10" />
          {t("signup.or")}
          <span className="h-px flex-1 bg-white/10" />
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          <label className="flex flex-col gap-2 text-sm">
            {t("signup.fullName")}
            <input
              type="text"
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              className="rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm text-white outline-none focus:border-orange-400/70"
              placeholder="Seu nome"
              required
              disabled={loading}
            />
          </label>
          <label className="flex flex-col gap-2 text-sm">
            {t("signup.company")}
            <input
              type="text"
              value={companyName}
              onChange={(event) => setCompanyName(event.target.value)}
              className="rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm text-white outline-none focus:border-orange-400/70"
              placeholder="Empresa"
              required
              disabled={loading}
            />
          </label>
          <label className="flex flex-col gap-2 text-sm">
            {t("signup.phone")}
            <input
              type="tel"
              value={phone}
              onChange={(event) => setPhone(event.target.value)}
              className="rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm text-white outline-none focus:border-orange-400/70"
              placeholder="+55 11 99999-0000"
              required
              disabled={loading}
            />
          </label>
          <label className="flex flex-col gap-2 text-sm">
            {t("signup.email")}
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
            {t("signup.password")}
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
          <fieldset className="space-y-2 text-sm">
            <legend className="text-sm text-slate-300">{t("signup.lgpdTitle")}</legend>
            <label className="flex items-center gap-2 text-sm text-slate-300">
              <input
                type="radio"
                name="marketing-consent"
                value="opt-in"
                checked={marketingConsent === "opt-in"}
                onChange={() => setMarketingConsent("opt-in")}
                disabled={loading}
              />
              {t("signup.optIn")}
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-300">
              <input
                type="radio"
                name="marketing-consent"
                value="opt-out"
                checked={marketingConsent === "opt-out"}
                onChange={() => setMarketingConsent("opt-out")}
                disabled={loading}
              />
              {t("signup.optOut")}
            </label>
          </fieldset>
          <button
            type="submit"
            disabled={loading || !hasSupabaseConfig}
            className="w-full rounded-full bg-orange-500 px-6 py-3 text-sm font-semibold text-slate-950 transition hover:bg-orange-400 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {loading ? t("signup.loading") : t("signup.submit")}
          </button>
        </form>

        <p className="text-center text-sm text-slate-400">
          {t("signup.loginPrompt")}{" "}
          <Link to="/login" className="text-orange-300 hover:text-orange-200">
            {t("signup.loginLink")}
          </Link>
        </p>
      </div>
    </div>
  );
}

export default Signup;
