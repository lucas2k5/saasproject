import { motion } from "framer-motion";
import { CheckCircle2 } from "lucide-react";
import { fadeUp, stagger } from "./animations";
import { Card } from "../ui/card";

const modules = [
  "Overview",
  "Campaigns",
  "Abandoned Carts",
  "Analytics",
  "AI Advisor",
  "Playbooks"
];

function DashboardShowcase() {
  return (
    <motion.section
      id="product"
      className="mx-auto grid w-full max-w-6xl gap-10"
      variants={fadeUp}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.2 }}
    >
      <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
        <motion.div className="grid gap-4" variants={fadeUp}>
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-cyan-300">
            Dashboards
          </p>
          <h2 className="text-3xl font-semibold text-white sm:text-4xl">
            Uma central visual para operar marketing orientado por dados.
          </h2>
          <p className="text-base text-slate-300">
            Crie paines por campanha, canal ou squad e acompanhe impacto em tempo real.
          </p>
          <div className="grid gap-3">
            {[
              "Indicadores de receita e engajamento em um unico lugar",
              "Alertas automaticos para quedas de performance",
              "Relatorios prontos para apresentar ao board"
            ].map((item) => (
              <motion.div
                key={item}
                className="flex items-center gap-3 text-sm text-slate-300"
                variants={fadeUp}
              >
                <CheckCircle2 className="h-4 w-4 text-cyan-300" />
                {item}
              </motion.div>
            ))}
          </div>
        </motion.div>

        <motion.div variants={fadeUp}>
          <Card className="grid gap-4 border border-white/10 bg-gradient-to-br from-[#0b1b2e] via-[#0f2a46] to-[#0b1b2e] text-white">
            <div className="flex items-center justify-between text-xs text-slate-300">
              <span>Preview dashboard</span>
              <span>Live</span>
            </div>
            <motion.div className="grid gap-3" variants={stagger}>
              {["Receita", "Conversoes", "ROI", "Retencao"].map((metric) => (
                <motion.div
                  key={metric}
                  className="flex items-center justify-between rounded-2xl border border-white/10 bg-[#0f3554]/80 px-4 py-3"
                  variants={fadeUp}
                  whileHover={{ y: -4 }}
                >
                  <p className="text-sm text-slate-200">{metric}</p>
                  <span className="text-sm font-semibold text-white">+12%</span>
                </motion.div>
              ))}
            </motion.div>
            <motion.div className="grid grid-cols-2 gap-3" variants={stagger}>
              {modules.map((module) => (
                <motion.div
                  key={module}
                  className="rounded-xl border border-white/10 bg-[#14395a]/80 px-3 py-2 text-xs text-slate-200"
                  variants={fadeUp}
                  whileHover={{ y: -4 }}
                >
                  {module}
                </motion.div>
              ))}
            </motion.div>
          </Card>
        </motion.div>
      </div>
    </motion.section>
  );
}

export default DashboardShowcase;
