import DashboardLayout from "../components/DashboardLayout";
import { useLocale } from "../context/LocaleContext";

function Playbooks() {
  const { t } = useLocale();

  return (
    <DashboardLayout
      title={t("playbooks.title")}
      subtitle={t("playbooks.subtitle")}
      label={t("playbooks.label")}
    >
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[
          { label: t("playbooks.stat.active"), value: "14" },
          { label: t("playbooks.stat.running"), value: "6" },
          { label: t("playbooks.stat.automations"), value: "22" },
          { label: t("playbooks.stat.customizations"), value: "38" }
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
              {t("playbooks.panel.suggestedTitle")}
            </h2>
            <p className="text-sm text-[color:var(--muted)]">
              {t("playbooks.panel.suggestedSubtitle")}
            </p>
          </div>
          <div className="mt-6 grid gap-3">
            {[
              t("playbooks.item.recovery"),
              t("playbooks.item.upsell"),
              t("playbooks.item.onboarding")
            ].map((item) => (
              <div
                className="flex items-center justify-between rounded-2xl border border-[color:var(--stroke)] bg-[color:var(--bg-soft)] px-4 py-3 text-sm"
                key={item}
              >
                <p className="text-[color:var(--ink)]">{item}</p>
                <span className="text-xs uppercase tracking-[0.2em] text-[color:var(--muted)]">
                  {t("playbooks.status.configure")}
                </span>
              </div>
            ))}
          </div>
        </article>
        <article className="rounded-3xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-6 shadow-[0_22px_40px_rgba(8,12,24,0.3)]">
          <div>
            <h2 className="text-lg font-semibold text-[color:var(--ink)]">
              {t("playbooks.panel.templatesTitle")}
            </h2>
            <p className="text-sm text-[color:var(--muted)]">
              {t("playbooks.panel.templatesSubtitle")}
            </p>
          </div>
          <div className="mt-6 space-y-4">
            {[
              t("playbooks.template.cart"),
              t("playbooks.template.lead"),
              t("playbooks.template.reactivation")
            ].map((label, index) => (
              <div
                className="grid grid-cols-[140px_1fr] items-center gap-4 text-sm"
                key={label}
              >
                <span className="text-[color:var(--muted)]">{label}</span>
                  <div className="h-2 rounded-full bg-[color:var(--stroke)]">
                    <div
                      className="h-2 rounded-full bg-gradient-to-r from-[color:var(--accent-2)] to-transparent"
                      style={{ width: `${82 - index * 12}%` }}
                    />
                  </div>
              </div>
            ))}
          </div>
        </article>
      </section>
    </DashboardLayout>
  );
}

export default Playbooks;
