import { motion } from "framer-motion";
import {
  BarChart3,
  Database,
  ShieldCheck,
  Sparkles,
  UserRound,
  Zap
} from "lucide-react";
import { fadeUp, stagger } from "./animations";
import { Card, CardDescription, CardHeader, CardTitle } from "../ui/card";

const features = [
  {
    title: "Analytics unificado",
    description:
      "Consolide dados de todas as plataformas em um único painel inteligente.",
    icon: BarChart3,
    accent: "from-orange-500 to-amber-400"
  },
  {
    title: "Automação inteligente",
    description: "Crie fluxos automatizados baseados em comportamento em tempo real.",
    icon: Zap,
    accent: "from-sky-500 to-cyan-400"
  },
  {
    title: "Segmentação avançada",
    description: "Use IA para identificar segmentos e personalizar comunicações.",
    icon: Sparkles,
    accent: "from-fuchsia-500 to-pink-400"
  },
  {
    title: "Previsão de churn",
    description: "Antecipe abandono e ative campanhas de retenção automaticamente.",
    icon: Database,
    accent: "from-emerald-500 to-teal-400"
  },
  {
    title: "Customer 360°",
    description: "Visão completa do cliente com dados unificados de todas as fontes.",
    icon: UserRound,
    accent: "from-rose-500 to-red-400"
  },
  {
    title: "Compliance & LGPD",
    description: "Gestão centralizada de consentimentos e dados sensíveis.",
    icon: ShieldCheck,
    accent: "from-violet-500 to-indigo-400"
  }
];

function Features() {
  return (
    <motion.section
      id="features"
      className="mx-auto grid w-full max-w-6xl gap-12"
      variants={fadeUp}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.2 }}
    >
      <motion.div className="mx-auto grid max-w-3xl gap-4 text-center" variants={fadeUp}>
        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-orange-400">
          Recursos
        </p>
        <h2 className="text-3xl font-semibold text-white sm:text-4xl">
          Tudo o que você precisa para{" "}
          <span className="bg-gradient-to-r from-orange-400 to-cyan-300 bg-clip-text text-transparent">
            escalar
          </span>
        </h2>
        <p className="text-base text-slate-300">
          Uma plataforma completa para unificar, analisar e otimizar todas as suas
          operações de marketing.
        </p>
      </motion.div>

      <motion.div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3" variants={stagger}>
        {features.map((feature) => {
          const Icon = feature.icon;
          return (
            <motion.div
              key={feature.title}
              variants={fadeUp}
              whileHover={{ y: -6 }}
              transition={{ duration: 0.2 }}
            >
              <Card className="h-full border-white/10 bg-slate-950/60">
                <CardHeader>
                  <div
                    className={`flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br ${feature.accent}`}
                  >
                    <Icon className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle>{feature.title}</CardTitle>
                  <CardDescription>{feature.description}</CardDescription>
                  <button className="mt-2 inline-flex items-center gap-2 text-sm font-semibold text-orange-300">
                    Saiba mais <span>→</span>
                  </button>
                </CardHeader>
              </Card>
            </motion.div>
          );
        })}
      </motion.div>
    </motion.section>
  );
}

export default Features;
