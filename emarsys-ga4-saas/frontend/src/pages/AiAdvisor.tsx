import DashboardLayout from "../components/DashboardLayout";
import { useLocale } from "../context/LocaleContext";

function AiAdvisor() {
  const { t } = useLocale();

  return (
    <DashboardLayout
      title={t("advisor.title")}
      subtitle={t("advisor.subtitle")}
      label={t("advisor.label")}
    >
      <section className="flex min-h-[560px] flex-col gap-6 rounded-3xl border border-[color:var(--stroke)] bg-[color:var(--surface)] p-6 shadow-[0_22px_40px_rgba(8,12,24,0.3)]">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[rgba(255,106,61,0.2)] text-[color:var(--accent)]">
              ✶
            </div>
            <div>
              <h2 className="text-lg font-semibold text-[color:var(--ink)]">
                {t("advisor.headerTitle")}
              </h2>
              <p className="text-sm text-[color:var(--muted)]">
                {t("advisor.headerSubtitle")}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              className="rounded-full border border-[color:var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[color:var(--ink)] opacity-80 transition hover:opacity-100"
              type="button"
            >
              {t("advisor.newBrief")}
            </button>
            <button
              className="rounded-full bg-[color:var(--accent)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-slate-950 shadow-[0_12px_30px_rgba(255,106,61,0.35)] transition hover:bg-[#ff8a66]"
              type="button"
            >
              {t("advisor.generate")}
            </button>
          </div>
        </div>

        <div className="flex flex-1 flex-col gap-4">
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[color:var(--surface-strong)] text-xs font-semibold text-[color:var(--ink)]">
              AI
            </div>
            <div className="max-w-[75%] rounded-2xl border border-[color:var(--stroke)] bg-[color:var(--bg-soft)] px-4 py-3 text-sm text-[color:var(--ink)]">
              {t("advisor.message.assistant1")}
            </div>
          </div>
          <div className="flex items-start justify-end gap-3">
            <div className="max-w-[75%] rounded-2xl border border-[color:var(--stroke)] bg-[rgba(255,106,61,0.12)] px-4 py-3 text-sm text-[color:var(--ink)]">
              {t("advisor.message.user1")}
            </div>
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[rgba(255,106,61,0.2)] text-xs font-semibold text-[color:var(--accent)]">
              JD
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[color:var(--surface-strong)] text-xs font-semibold text-[color:var(--ink)]">
              AI
            </div>
            <div className="max-w-[75%] rounded-2xl border border-[color:var(--stroke)] bg-[color:var(--bg-soft)] px-4 py-3 text-sm text-[color:var(--ink)]">
              {t("advisor.message.assistant2")}
            </div>
          </div>
        </div>

        <form
          className="flex items-center gap-3 rounded-full border border-[color:var(--stroke)] bg-[color:var(--bg-soft)] px-4 py-2"
          onSubmit={(event) => event.preventDefault()}
        >
          <input
            type="text"
            placeholder={t("advisor.placeholder")}
            className="flex-1 bg-transparent text-sm text-[color:var(--ink)] placeholder:text-[color:var(--muted)] focus:outline-none"
          />
          <button
            className="flex h-10 w-10 items-center justify-center rounded-full bg-[color:var(--accent)] text-slate-950"
            type="submit"
          >
            ➤
          </button>
        </form>
      </section>
    </DashboardLayout>
  );
}

export default AiAdvisor;
