import { motion } from "framer-motion";
import { fadeUp, stagger } from "./animations";
import { Badge } from "../ui/badge";

const integrations = [
  { label: "Emarsys", color: "#0a6ed1", mark: "E" },
  { label: "Google Analytics 4", color: "#0b84f3", mark: "GA4" },
  { label: "Salesforce", color: "#1d4ed8", mark: "SF" },
  { label: "HubSpot", color: "#0f7bf2", mark: "HS" },
  { label: "VTEX", color: "#0284c7", mark: "VT" },
  { label: "Shopify", color: "#2563eb", mark: "SH" },
  { label: "Meta Ads", color: "#0ea5e9", mark: "MA" },
  { label: "Google Ads", color: "#38bdf8", mark: "GA" }
];

function Integrations() {
  return (
    <motion.section
      id="integrations"
      className="mx-auto grid w-full max-w-6xl gap-10"
      variants={fadeUp}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.2 }}
    >
      <motion.div className="flex flex-col gap-3" variants={fadeUp}>
        <Badge variant="highlight">Integrações</Badge>
        <h2 className="text-3xl font-semibold text-white sm:text-4xl">
          Conecte suas ferramentas favoritas em minutos.
        </h2>
        <p className="max-w-2xl text-base text-slate-300">
          Integrações nativas para manter seus dados sincronizados e prontos para analise.
        </p>
      </motion.div>
      <motion.div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" variants={stagger}>
        {integrations.map((item) => (
          <motion.div
            key={item.label}
            className="flex items-center gap-4 rounded-full border border-white/10 bg-slate-950/50 px-5 py-3 text-sm font-semibold text-slate-200"
            variants={fadeUp}
            whileHover={{ y: -4 }}
          >
            <span
              className="flex h-9 min-w-[36px] items-center justify-center rounded-full text-xs font-bold text-white shadow-[0_10px_20px_rgba(15,23,42,0.4)]"
              style={{ backgroundColor: item.color }}
            >
              {item.mark}
            </span>
            {item.label}
          </motion.div>
        ))}
      </motion.div>
    </motion.section>
  );
}

export default Integrations;
