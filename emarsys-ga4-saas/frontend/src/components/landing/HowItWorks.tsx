import { motion } from "framer-motion";
import { CheckCircle2, Database, Brain, Megaphone, ShoppingCart } from "lucide-react";
import { fadeUp, stagger } from "./animations";
import { Badge } from "../ui/badge";

const modules = [
  {
    title: "Data Hub",
    subtitle: "Central de dados",
    description:
      "Unifique todos os seus dados de marketing em um data warehouse inteligente.",
    icon: Database,
    accent: "from-cyan-500 to-blue-500",
    featured: true
  },
  {
    title: "AI Insights",
    subtitle: "Inteligencia artificial",
    description:
      "Algoritmos de IA para descobrir padrões e gerar recomendações acionáveis.",
    icon: Brain,
    accent: "from-fuchsia-500 to-pink-500"
  },
  {
    title: "Campaign Studio",
    subtitle: "Gestao de campanhas",
    description:
      "Orquestre campanhas multicanal com automacao e personalizacao em escala.",
    icon: Megaphone,
    accent: "from-orange-500 to-amber-500"
  },
  {
    title: "Commerce Analytics",
    subtitle: "E-commerce intelligence",
    description:
      "Analise comportamento de compra e otimize conversoes com visoes avancadas.",
    icon: ShoppingCart,
    accent: "from-emerald-500 to-teal-500"
  }
];

function HowItWorks() {
  const activeModule = modules[0];
  const ActiveIcon = activeModule.icon;

  return (
    <motion.section
      id="modules"
      className="mx-auto grid w-full max-w-6xl gap-10"
      variants={fadeUp}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.2 }}
    >
      <motion.div className="mx-auto grid max-w-3xl gap-4 text-center" variants={fadeUp}>
        <Badge variant="highlight">Módulos</Badge>
        <h2 className="text-3xl font-semibold text-white sm:text-4xl">
          Uma plataforma,{" "}
          <span className="bg-gradient-to-r from-cyan-300 to-blue-400 bg-clip-text text-transparent">
            infinitas possibilidades
          </span>
        </h2>
      </motion.div>

      <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-start">
        <motion.div className="grid gap-4" variants={stagger}>
          {modules.map((module) => {
            const Icon = module.icon;
            return (
              <motion.div
                key={module.title}
                className={`rounded-2xl border px-5 py-4 shadow-sm ${
                  module.featured
                    ? "border-orange-400/40 bg-white/5"
                    : "border-white/10 bg-slate-950/40"
                }`}
                variants={fadeUp}
                whileHover={{ y: -4 }}
              >
                <div className="flex items-start gap-4">
                  <div
                    className={`flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br ${module.accent}`}
                  >
                    <Icon className="h-6 w-6 text-white" />
                  </div>
                  <div className="grid gap-2">
                    <div className="flex flex-wrap items-center gap-3">
                      <h3 className="text-lg font-semibold text-white">{module.title}</h3>
                      <span className="text-sm text-slate-400">· {module.subtitle}</span>
                    </div>
                    <p className="text-sm text-slate-300">{module.description}</p>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </motion.div>

        <motion.div
          className="rounded-3xl border border-white/10 bg-gradient-to-br from-slate-900/80 to-slate-950/90 p-6"
          variants={fadeUp}
        >
          <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-cyan-500/20 via-blue-500/10 to-slate-950/60 p-6">
            <div className="flex h-36 items-center justify-center rounded-2xl border border-white/10 bg-white/5">
              <ActiveIcon className="h-12 w-12 text-cyan-200" />
            </div>
          </div>
          <div className="mt-6 grid gap-3">
            <h3 className="text-2xl font-semibold text-white">{activeModule.title}</h3>
            <p className="text-sm text-slate-300">{activeModule.description}</p>
            <div className="mt-2 grid gap-2 text-sm text-slate-300">
              {[
                "ETL automatizado de multiplas fontes",
                "Data quality em tempo real",
                "Historico completo de interacoes",
                "APIs abertas para customizacao"
              ].map((item) => (
                <div key={item} className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  {item}
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </motion.section>
  );
}

export default HowItWorks;
