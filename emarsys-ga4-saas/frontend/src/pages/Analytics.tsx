import DashboardLayout from "../components/DashboardLayout";
import { useLocale } from "../context/LocaleContext";

function Analytics() {
  const { t } = useLocale();

  return (
    <DashboardLayout
      title={t("analytics.title")}
      subtitle={t("analytics.subtitle")}
      label={t("analytics.label")}
    >
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[
          { label: t("analytics.stat.sessions"), value: "482k" },
          { label: t("analytics.stat.activeUsers"), value: "118k" },
          { label: t("analytics.stat.avgTime"), value: "4m 22s" },
          { label: t("analytics.stat.engagement"), value: "62%" }
        ].map((item) => (
          <article
            className="rounded-2xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-5"
            key={item.label}
          >
            <p className="text-xs uppercase tracking-[0.25em] text-[color:var(--muted)]">
              {item.label}
            </p>
            <p className="mt-2 text-2xl font-semibold text-[color:var(--ink)]">
              {item.value}
            </p>
          </article>
        ))}
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.2fr_1fr]">
        <article className="rounded-3xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-6 shadow-[0_22px_40px_rgba(8,12,24,0.3)]">
          <div>
            <h2 className="text-lg font-semibold text-[color:var(--ink)]">
              {t("analytics.panel.journeysTitle")}
            </h2>
            <p className="text-sm text-[color:var(--muted)]">
              {t("analytics.panel.journeysSubtitle")}
            </p>
          </div>
          <div className="mt-6 space-y-4">
            {[
              t("analytics.journey.landing"),
              t("analytics.journey.cart"),
              t("analytics.journey.email"),
              t("analytics.journey.referral")
            ].map((label, index) => (
              <div
                className="grid grid-cols-[150px_1fr] items-center gap-4 text-sm"
                key={label}
              >
                <span className="text-[color:var(--muted)]">{label}</span>
                  <div className="h-2 rounded-full bg-[color:var(--stroke)]">
                    <div
                      className="h-2 rounded-full bg-gradient-to-r from-[color:var(--accent-2)] to-transparent"
                      style={{ width: `${90 - index * 12}%` }}
                    />
                  </div>
              </div>
            ))}
          </div>
        </article>
        <article className="rounded-3xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-6 shadow-[0_22px_40px_rgba(8,12,24,0.3)]">
          <div>
            <h2 className="text-lg font-semibold text-[color:var(--ink)]">
              {t("analytics.panel.alertsTitle")}
            </h2>
            <p className="text-sm text-[color:var(--muted)]">
              {t("analytics.panel.alertsSubtitle")}
            </p>
          </div>
          <div className="mt-6 grid gap-3">
            {[
              t("analytics.alert.mobile"),
              t("analytics.alert.paid"),
              t("analytics.alert.bounce")
            ].map((item) => (
              <div
                className="flex items-center justify-between rounded-2xl border border-[color:var(--stroke)] bg-[color:var(--bg-soft)] px-4 py-3 text-sm"
                key={item}
              >
                <p className="text-[color:var(--ink)]">{item}</p>
                <span className="text-xs uppercase tracking-[0.2em] text-[color:var(--muted)]">
                  {t("analytics.status.monitor")}
                </span>
              </div>
            ))}
          </div>
        </article>
      </section>
    </DashboardLayout>
  );
}

export default Analytics;
