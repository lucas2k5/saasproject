import DashboardLayout from "../components/DashboardLayout";
import { useLocale } from "../context/LocaleContext";

function Campaigns() {
  const { t } = useLocale();

  return (
    <DashboardLayout
      title={t("campaigns.title")}
      subtitle={t("campaigns.subtitle")}
      label={t("campaigns.label")}
    >
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[
          { label: t("campaigns.stat.active"), value: "28" },
          { label: t("campaigns.stat.sendsToday"), value: "12.840" },
          { label: t("campaigns.stat.ctr"), value: "3.4%" },
          { label: t("campaigns.stat.conversions"), value: "1.294" }
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
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold text-[color:var(--ink)]">
                {t("campaigns.panel.topTitle")}
              </h2>
              <p className="text-sm text-[color:var(--muted)]">
                {t("campaigns.panel.topSubtitle")}
              </p>
            </div>
            <div className="text-xs uppercase tracking-[0.2em] text-[color:var(--muted)]">
              {t("campaigns.panel.last7Days")}
            </div>
          </div>
          <div className="mt-6 space-y-4">
            {[
              t("campaigns.item.emailPro"),
              t("campaigns.item.cartRescue"),
              t("campaigns.item.winback"),
              t("campaigns.item.nurture")
            ].map((label, index) => (
              <div
                className="grid grid-cols-[120px_1fr] items-center gap-4 text-sm"
                key={label}
              >
                <span className="text-[color:var(--muted)]">{label}</span>
                  <div className="h-2 rounded-full bg-[color:var(--stroke)]">
                    <div
                      className="h-2 rounded-full bg-gradient-to-r from-[color:var(--accent-2)] to-transparent"
                      style={{ width: `${88 - index * 14}%` }}
                    />
                  </div>
              </div>
            ))}
          </div>
        </article>
        <article className="rounded-3xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-6 shadow-[0_22px_40px_rgba(8,12,24,0.3)]">
          <div>
            <h2 className="text-lg font-semibold text-[color:var(--ink)]">
              {t("campaigns.panel.testTitle")}
            </h2>
            <p className="text-sm text-[color:var(--muted)]">
              {t("campaigns.panel.testSubtitle")}
            </p>
          </div>
          <div className="mt-6 grid gap-3">
            {[
              t("campaigns.test.cta"),
              t("campaigns.test.subject"),
              t("campaigns.test.timing"),
              t("campaigns.test.segment")
            ].map((item) => (
              <div
                className="flex items-center justify-between rounded-2xl border border-[color:var(--stroke)] bg-[color:var(--bg-soft)] px-4 py-3 text-sm"
                key={item}
              >
                <p className="text-[color:var(--ink)]">{item}</p>
                <span className="text-xs uppercase tracking-[0.2em] text-[color:var(--muted)]">
                  {t("campaigns.status.inProgress")}
                </span>
              </div>
            ))}
          </div>
        </article>
      </section>
    </DashboardLayout>
  );
}

export default Campaigns;
