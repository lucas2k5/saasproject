import type { ChangeEvent } from "react";
import type { Locale } from "../i18n/translations";
import DashboardLayout from "../components/DashboardLayout";
import { useAuth } from "../context/AuthContext";
import { useLocale } from "../context/LocaleContext";

function Profile() {
  const { user } = useAuth();
  const { t, locale, setLocale } = useLocale();
  const metadata = user?.user_metadata as Record<string, unknown> | undefined;
  const fullName = typeof metadata?.full_name === "string" ? metadata.full_name : "";
  const companyName =
    typeof metadata?.company_name === "string" ? metadata.company_name : "";
  const phone = typeof metadata?.phone === "string" ? metadata.phone : "";
  const marketingOptIn =
    typeof metadata?.marketing_opt_in === "boolean" ? metadata.marketing_opt_in : null;

  const handleLocaleChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const nextLocale: Locale = event.target.value === "en-US" ? "en-US" : "pt-BR";
    void setLocale(nextLocale);
  };

  return (
    <DashboardLayout
      title={t("profile.title")}
      subtitle={t("profile.subtitle")}
      label={t("profile.label")}
    >
      <section className="grid gap-4 lg:grid-cols-3">
        <article className="rounded-3xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-6 shadow-[0_22px_40px_rgba(8,12,24,0.3)]">
          <h2 className="text-lg font-semibold text-[color:var(--ink)]">
            {t("profile.personalTitle")}
          </h2>
          <div className="mt-6 grid gap-4 text-sm">
            <div>
              <p className="text-xs uppercase tracking-[0.25em] text-[color:var(--muted)]">
                {t("profile.fullName")}
              </p>
              <p className="mt-1 text-[color:var(--ink)]">
                {fullName || t("profile.notProvided")}
              </p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.25em] text-[color:var(--muted)]">
                {t("profile.email")}
              </p>
              <p className="mt-1 text-[color:var(--ink)]">
                {user?.email ?? t("profile.notProvided")}
              </p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.25em] text-[color:var(--muted)]">
                {t("profile.phone")}
              </p>
              <p className="mt-1 text-[color:var(--ink)]">
                {phone || t("profile.notProvided")}
              </p>
            </div>
          </div>
        </article>

        <article className="rounded-3xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-6 shadow-[0_22px_40px_rgba(8,12,24,0.3)]">
          <h2 className="text-lg font-semibold text-[color:var(--ink)]">
            {t("profile.companyTitle")}
          </h2>
          <div className="mt-6 grid gap-4 text-sm">
            <div>
              <p className="text-xs uppercase tracking-[0.25em] text-[color:var(--muted)]">
                {t("profile.company")}
              </p>
              <p className="mt-1 text-[color:var(--ink)]">
                {companyName || t("profile.notProvided")}
              </p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.25em] text-[color:var(--muted)]">
                {t("profile.lgpd")}
              </p>
              <p className="mt-1 text-[color:var(--ink)]">
                {marketingOptIn === null
                  ? t("profile.notProvided")
                  : marketingOptIn
                    ? t("profile.lgpdOptIn")
                    : t("profile.lgpdOptOut")}
              </p>
            </div>
          </div>
        </article>

        <article className="rounded-3xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-6 shadow-[0_22px_40px_rgba(8,12,24,0.3)]">
          <h2 className="text-lg font-semibold text-[color:var(--ink)]">
            {t("profile.workspaceTitle")}
          </h2>
          <div className="mt-6 grid gap-4 text-sm">
            <div>
              <label
                htmlFor="language"
                className="text-xs uppercase tracking-[0.25em] text-[color:var(--muted)]"
              >
                {t("profile.language")}
              </label>
              <select
                id="language"
                value={locale}
                onChange={handleLocaleChange}
                className="mt-2 w-full rounded-2xl border border-[color:var(--stroke)] bg-[color:var(--surface-strong)] px-4 py-3 text-sm text-[color:var(--ink)] outline-none transition focus:border-[color:var(--accent)]"
              >
                <option value="pt-BR">{t("language.pt")}</option>
                <option value="en-US">{t("language.en")}</option>
              </select>
            </div>
          </div>
        </article>
      </section>
    </DashboardLayout>
  );
}

export default Profile;
