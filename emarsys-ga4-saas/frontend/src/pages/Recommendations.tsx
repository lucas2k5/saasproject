import DashboardLayout from "../components/DashboardLayout";
import { useLocale } from "../context/LocaleContext";

const productRecommendations = [
  {
    titleKey: "dashboard.recommendations.item.bundle.title",
    descriptionKey: "dashboard.recommendations.item.bundle.description",
    uplift: "+18%"
  },
  {
    titleKey: "dashboard.recommendations.item.crossSell.title",
    descriptionKey: "dashboard.recommendations.item.crossSell.description",
    uplift: "+12%"
  },
  {
    titleKey: "dashboard.recommendations.item.upsell.title",
    descriptionKey: "dashboard.recommendations.item.upsell.description",
    uplift: "+9%"
  },
  {
    titleKey: "dashboard.recommendations.item.trending.title",
    descriptionKey: "dashboard.recommendations.item.trending.description",
    uplift: "+7%"
  }
];

function Recommendations() {
  const { t } = useLocale();

  return (
    <DashboardLayout
      title={t("recommendations.title")}
      subtitle={t("recommendations.subtitle")}
      label={t("recommendations.label")}
    >
      <section className="rounded-3xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-6 shadow-[0_22px_40px_rgba(8,12,24,0.3)]">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-[color:var(--ink)]">
              {t("dashboard.recommendations.title")}
            </h2>
            <p className="text-sm text-[color:var(--muted)]">
              {t("dashboard.recommendations.subtitle")}
            </p>
          </div>
          <span className="rounded-full border border-[color:var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[color:var(--muted)]">
            {t("dashboard.recommendations.cta")}
          </span>
        </div>
        <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {productRecommendations.map((item) => (
            <div
              key={item.titleKey}
              className="rounded-2xl border border-[color:var(--stroke)] bg-[color:var(--bg-soft)] p-5"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold text-[color:var(--ink)]">
                    {t(item.titleKey)}
                  </p>
                  <p className="mt-2 text-xs text-[color:var(--muted)]">
                    {t(item.descriptionKey)}
                  </p>
                </div>
                <span className="rounded-full bg-[color:var(--positive-bg)] px-2.5 py-1 text-xs font-semibold text-[color:var(--positive-text)]">
                  {item.uplift}
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>
    </DashboardLayout>
  );
}

export default Recommendations;
