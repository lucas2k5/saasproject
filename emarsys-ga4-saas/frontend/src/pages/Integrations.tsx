import { useState } from "react";
import DashboardLayout from "../components/DashboardLayout";
import emarsysLogo from "../assets/logos/emarsys.svg";
import googleAnalyticsLogo from "../assets/logos/google-analytics.svg";
import hubspotLogo from "../assets/logos/hubspot.svg";
import salesforceLogo from "../assets/logos/salesforce.svg";
import vtexLogo from "../assets/logos/vtex.svg";
import { useLocale } from "../context/LocaleContext";

type IntegrationTab = "marketing" | "whatsapp";

type MarketingTool = {
  name: string;
  logo: string;
  logoClassName?: string;
  textMark?: string;
  descriptionKey: string;
  syncKey: string;
  connected: boolean;
};

function Integrations() {
  const { t } = useLocale();
  const [activeTab, setActiveTab] = useState<IntegrationTab>("marketing");

  const marketingTools: MarketingTool[] = [
    {
      name: "Emarsys",
      logo: emarsysLogo,
      descriptionKey: "integrations.marketing.tool.emarsys",
      syncKey: "integrations.sync.realtime",
      connected: true
    },
    {
      name: "HubSpot",
      logo: hubspotLogo,
      descriptionKey: "integrations.marketing.tool.hubspot",
      syncKey: "integrations.sync.hourly",
      connected: true
    },
    {
      name: "Salesforce Marketing Cloud",
      logo: salesforceLogo,
      logoClassName: "h-7 max-w-[48px]",
      descriptionKey: "integrations.marketing.tool.sfmc",
      syncKey: "integrations.sync.hourly",
      connected: false
    },
    {
      name: "VTEX",
      logo: vtexLogo,
      descriptionKey: "integrations.marketing.tool.vtex",
      syncKey: "integrations.sync.realtime",
      connected: true
    },
    {
      name: "Klaviyo",
      logo: emarsysLogo,
      textMark: "K",
      descriptionKey: "integrations.marketing.tool.klaviyo",
      syncKey: "integrations.sync.hourly",
      connected: true
    },
    {
      name: "Google Analytics 4",
      logo: googleAnalyticsLogo,
      logoClassName: "h-6 max-w-[44px]",
      descriptionKey: "integrations.marketing.tool.ga4",
      syncKey: "integrations.sync.realtime",
      connected: true
    },
    {
      name: "Core API",
      logo: emarsysLogo,
      descriptionKey: "integrations.marketing.tool.core",
      syncKey: "integrations.sync.realtime",
      connected: true
    }
  ];

  const connectedTools = marketingTools.filter((tool) => tool.connected).length;

  const whatsappFlows = [
    { labelKey: "integrations.whatsapp.flow.abandoned", conversion: "18.4%" },
    { labelKey: "integrations.whatsapp.flow.winback", conversion: "11.2%" },
    { labelKey: "integrations.whatsapp.flow.postPurchase", conversion: "22.9%" },
    { labelKey: "integrations.whatsapp.flow.promotional", conversion: "8.1%" }
  ];

  return (
    <DashboardLayout
      title={t("integrations.title")}
      subtitle={t("integrations.subtitle")}
      label={t("integrations.label")}
    >
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[
          {
            label: t("integrations.stat.connected"),
            value: `${connectedTools}/${marketingTools.length}`
          },
          { label: t("integrations.stat.available"), value: `${marketingTools.length}` },
          { label: t("integrations.stat.whatsappTemplates"), value: "24" },
          { label: t("integrations.stat.campaignsLive"), value: "9" }
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

      <section className="rounded-3xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-6 shadow-[0_22px_40px_rgba(8,12,24,0.3)]">
        <div className="mb-6 flex flex-wrap gap-2">
          <button
            className={`rounded-xl border px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] transition ${
              activeTab === "marketing"
                ? "border-[color:var(--accent)] bg-[rgba(255,122,61,0.16)] text-[color:var(--ink)]"
                : "border-[color:var(--stroke)] bg-[color:var(--bg-soft)] text-[color:var(--muted)] hover:text-[color:var(--ink)]"
            }`}
            type="button"
            onClick={() => setActiveTab("marketing")}
          >
            {t("integrations.tabs.marketing")}
          </button>
          <button
            className={`rounded-xl border px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] transition ${
              activeTab === "whatsapp"
                ? "border-[color:var(--accent)] bg-[rgba(255,122,61,0.16)] text-[color:var(--ink)]"
                : "border-[color:var(--stroke)] bg-[color:var(--bg-soft)] text-[color:var(--muted)] hover:text-[color:var(--ink)]"
            }`}
            type="button"
            onClick={() => setActiveTab("whatsapp")}
          >
            {t("integrations.tabs.whatsapp")}
          </button>
        </div>

        {activeTab === "marketing" ? (
          <div>
            <div className="mb-5">
              <h2 className="text-lg font-semibold text-[color:var(--ink)]">
                {t("integrations.marketing.title")}
              </h2>
              <p className="text-sm text-[color:var(--muted)]">
                {t("integrations.marketing.subtitle")}
              </p>
            </div>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {marketingTools.map((tool) => (
                <article
                  className="rounded-2xl border border-[color:var(--stroke)] bg-[color:var(--bg-soft)] p-5"
                  key={tool.name}
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-white shadow-[0_8px_20px_rgba(0,0,0,0.2)]">
                      {tool.textMark ? (
                        <span className="text-sm font-semibold text-slate-900">
                          {tool.textMark}
                        </span>
                      ) : (
                        <img
                          src={tool.logo}
                          alt={`${tool.name} logo`}
                          className={`w-auto object-contain ${
                            tool.logoClassName ?? "h-6 max-w-[38px]"
                          }`}
                        />
                      )}
                    </span>
                    <span
                      className={`rounded-full px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.2em] ${
                        tool.connected
                          ? "bg-[rgba(36,213,160,0.14)] text-[#24d5a0]"
                          : "bg-[rgba(244,180,0,0.14)] text-[#f4b400]"
                      }`}
                    >
                      {tool.connected
                        ? t("integrations.status.connected")
                        : t("integrations.status.available")}
                    </span>
                  </div>
                  <h3 className="mt-4 text-sm font-semibold text-[color:var(--ink)]">
                    {tool.name}
                  </h3>
                  <p className="mt-2 min-h-[40px] text-xs text-[color:var(--muted)]">
                    {t(tool.descriptionKey)}
                  </p>
                  <div className="mt-4 flex items-center justify-between text-[11px] uppercase tracking-[0.14em] text-[color:var(--muted)]">
                    <span>{t("integrations.channel.marketing")}</span>
                    <span>{t(tool.syncKey)}</span>
                  </div>
                </article>
              ))}
            </div>
          </div>
        ) : (
          <div className="grid gap-4 xl:grid-cols-[1.05fr_1fr]">
            <article className="rounded-2xl border border-[color:var(--stroke)] bg-[color:var(--bg-soft)] p-5">
              <h2 className="text-lg font-semibold text-[color:var(--ink)]">
                {t("integrations.whatsapp.title")}
              </h2>
              <p className="text-sm text-[color:var(--muted)]">
                {t("integrations.whatsapp.subtitle")}
              </p>

              <div className="mt-5 grid gap-3 md:grid-cols-3">
                {[
                  {
                    label: t("integrations.whatsapp.number"),
                    value: "+55 11 97000-1000"
                  },
                  {
                    label: t("integrations.whatsapp.webhook"),
                    value: t("integrations.status.connected")
                  },
                  {
                    label: t("integrations.whatsapp.quality"),
                    value: t("integrations.whatsapp.qualityValue")
                  }
                ].map((item) => (
                  <div
                    className="rounded-xl border border-[color:var(--stroke)] bg-[color:var(--surface)] px-4 py-3"
                    key={item.label}
                  >
                    <p className="text-[11px] uppercase tracking-[0.15em] text-[color:var(--muted)]">
                      {item.label}
                    </p>
                    <p className="mt-2 text-sm font-semibold text-[color:var(--ink)]">
                      {item.value}
                    </p>
                  </div>
                ))}
              </div>

              <div className="mt-5 grid gap-3">
                {[
                  t("integrations.whatsapp.feature.templates"),
                  t("integrations.whatsapp.feature.audience"),
                  t("integrations.whatsapp.feature.optimization")
                ].map((feature) => (
                  <div
                    className="flex items-center justify-between rounded-xl border border-[color:var(--stroke)] bg-[color:var(--surface)] px-4 py-3 text-sm"
                    key={feature}
                  >
                    <span className="text-[color:var(--ink)]">{feature}</span>
                    <span className="text-[11px] uppercase tracking-[0.15em] text-[#24d5a0]">
                      {t("integrations.sync.realtime")}
                    </span>
                  </div>
                ))}
              </div>
            </article>

            <article className="rounded-2xl border border-[color:var(--stroke)] bg-[color:var(--bg-soft)] p-5">
              <h3 className="text-lg font-semibold text-[color:var(--ink)]">
                {t("integrations.whatsapp.automationsTitle")}
              </h3>
              <p className="text-sm text-[color:var(--muted)]">
                {t("integrations.whatsapp.automationsSubtitle")}
              </p>

              <div className="mt-5 space-y-3">
                {whatsappFlows.map((flow) => (
                  <div
                    className="rounded-xl border border-[color:var(--stroke)] bg-[color:var(--surface)] px-4 py-3"
                    key={flow.labelKey}
                  >
                    <div className="flex items-center justify-between gap-3 text-sm">
                      <p className="text-[color:var(--ink)]">{t(flow.labelKey)}</p>
                      <span className="text-[11px] uppercase tracking-[0.15em] text-[#24d5a0]">
                        {t("integrations.status.connected")}
                      </span>
                    </div>
                    <div className="mt-3 h-2 rounded-full bg-[color:var(--stroke)]">
                      <div
                        className="h-2 rounded-full bg-gradient-to-r from-[color:var(--accent-2)] to-transparent"
                        style={{ width: flow.conversion }}
                      />
                    </div>
                    <p className="mt-2 text-[11px] uppercase tracking-[0.14em] text-[color:var(--muted)]">
                      {t("integrations.whatsapp.conversion")} {flow.conversion}
                    </p>
                  </div>
                ))}
              </div>
            </article>
          </div>
        )}
      </section>
    </DashboardLayout>
  );
}

export default Integrations;
