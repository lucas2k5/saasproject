import { motion } from "framer-motion";
import { fadeUp, stagger } from "./animations";
import emarsysLogo from "../../assets/logos/emarsys.svg";
import salesforceLogo from "../../assets/logos/salesforce.svg";
import hubspotLogo from "../../assets/logos/hubspot.svg";
import vtexLogo from "../../assets/logos/vtex.svg";
import googleAnalyticsLogo from "../../assets/logos/google-analytics.svg";

type IntegrationLogo = {
  label: string;
  color: string;
  logo?: string;
  textMark?: string;
  logoClassName?: string;
};

const integrations: IntegrationLogo[] = [
  { label: "Emarsys", color: "#0a6ed1", logo: emarsysLogo },
  { label: "Salesforce", color: "#33b6ff", logo: salesforceLogo },
  { label: "HubSpot", color: "#ff7a3d", logo: hubspotLogo },
  { label: "VTEX", color: "#ff495c", logo: vtexLogo },
  { label: "Google Analytics", color: "#f4b400", logo: googleAnalyticsLogo },
  { label: "Klaviyo", color: "#2b2b2b", textMark: "K" }
];

function Integrations() {
  return (
    <motion.section
      id="integrations"
      className="relative mx-auto grid w-full max-w-6xl gap-10 text-center"
      variants={fadeUp}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.2 }}
    >
      <div className="pointer-events-none absolute inset-x-8 top-6 h-40 rounded-[40px] bg-[radial-gradient(circle,rgba(74,180,255,0.15),transparent_70%)] blur-2xl" />
      <motion.div className="flex flex-col items-center gap-3" variants={fadeUp}>
        <span className="text-[11px] font-semibold uppercase tracking-[0.35em] text-cyan-300">
          Integrações nativas com suas ferramentas favoritas
        </span>
        <h2 className="text-3xl font-semibold text-white sm:text-4xl">
          Conecte todas as suas{" "}
          <span className="bg-gradient-to-r from-orange-300 to-amber-400 bg-clip-text text-transparent">
            fontes
          </span>{" "}
          de{" "}
          <span className="bg-gradient-to-r from-emerald-300 to-cyan-300 bg-clip-text text-transparent">
            dados
          </span>
        </h2>
      </motion.div>

      <motion.div
        className="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6"
        variants={stagger}
      >
        {integrations.map((item) => (
          <motion.div
            key={item.label}
            className="group relative flex min-h-[116px] flex-col items-center justify-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-5 py-5 text-sm font-semibold text-slate-200 shadow-[0_20px_40px_rgba(4,10,22,0.35)] backdrop-blur"
            variants={fadeUp}
            whileHover={{ y: -6 }}
          >
            <span
              className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-slate-900 shadow-[0_10px_30px_rgba(0,0,0,0.25)]"
              style={{ color: item.color }}
            >
              {item.textMark ? (
                <span className="text-[13px] font-semibold text-slate-900">
                  {item.textMark}
                </span>
              ) : (
                <img
                  src={item.logo}
                  alt={`${item.label} logo`}
                  className={`w-auto object-contain ${
                    item.logoClassName ?? "h-6 max-w-[36px]"
                  }`}
                />
              )}
            </span>
            <span className="text-sm text-white">{item.label}</span>
            <span
              className="absolute bottom-2 right-3 h-2 w-2 rounded-full"
              style={{ backgroundColor: item.color }}
            />
          </motion.div>
        ))}
      </motion.div>

      <motion.div className="flex justify-center" variants={fadeUp}>
        <div className="relative inline-flex items-center justify-center">
          <motion.span
            className="absolute -inset-6 rounded-full bg-[conic-gradient(from_140deg,rgba(34,211,238,0.22),rgba(249,115,22,0.18),rgba(34,211,238,0.22))] blur-2xl"
            animate={{ rotate: 360 }}
            transition={{ duration: 12, repeat: Infinity, ease: "linear" }}
          />
          <motion.span
            className="absolute -inset-2 rounded-full border border-cyan-300/30 blur-md"
            animate={{ opacity: [0.2, 0.7, 0.2], scale: [1, 1.08, 1] }}
            transition={{ duration: 3.2, repeat: Infinity, ease: "easeInOut" }}
          />
          <motion.span
            className="absolute inset-0 rounded-full border border-white/10"
            animate={{ opacity: [0.2, 0.6, 0.2] }}
            transition={{ duration: 4.2, repeat: Infinity, ease: "easeInOut" }}
          />
          <div className="relative flex items-center justify-center rounded-full border border-white/10 bg-white/5 px-8 py-3 text-xs font-semibold uppercase tracking-[0.3em] text-cyan-200 shadow-[0_0_40px_rgba(59,130,246,0.35)]">
            Plataforma Omnichannel Unificada
          </div>
        </div>
      </motion.div>
    </motion.section>
  );
}

export default Integrations;
