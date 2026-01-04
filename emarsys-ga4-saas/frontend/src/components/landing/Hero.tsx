import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { fadeIn, fadeUp, stagger } from "./animations";
import { Button } from "../ui/button";

const metrics = [
  { value: "50+", label: "Métricas unificadas" },
  { value: "1.200+", label: "Empresas" },
  { value: "99,9%", label: "Taxa de automação" },
  { value: "4,9★", label: "Avaliação" }
];

function Hero() {
  return (
    <motion.section
      className="mx-auto grid w-full max-w-6xl gap-14 pb-10 pt-10"
      variants={fadeUp}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.3 }}
    >
      <motion.div className="grid gap-6 text-center" variants={stagger}>
        <motion.p
          className="text-xs font-semibold uppercase tracking-[0.35em] text-cyan-300"
          variants={fadeUp}
        >
          Unificando dados de plataformas de marketing e CRM
        </motion.p>
        <motion.h1
          className="font-display text-4xl font-bold text-white sm:text-5xl lg:text-6xl"
          variants={fadeUp}
        >
          KeepAIS transforma dados de marketing em insights confiáveis e planos de ação.
        </motion.h1>
        <motion.p
          className="mx-auto max-w-2xl text-base text-slate-300 sm:text-lg"
          variants={fadeUp}
        >
          Conecte Emarsys, GA4, Salesforce, HubSpot e VTEX para gerar dashboards em tempo
          real e acelerar decisões orientadas por dados.
        </motion.p>
        <motion.div className="flex flex-wrap justify-center gap-4" variants={fadeUp}>
          <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
            <Button asChild size="lg">
              <Link to="/dashboard">Ver planos</Link>
            </Button>
          </motion.div>
          <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
            <Button variant="outline" size="lg">
              Ver demonstração
            </Button>
          </motion.div>
        </motion.div>
      </motion.div>

      <motion.div
        className="grid gap-6 rounded-3xl border border-white/10 bg-white/5 p-8 shadow-[0_30px_60px_rgba(7,11,24,0.4)]"
        variants={fadeIn}
      >
        <div className="flex flex-wrap items-center justify-between gap-6">
          <div>
            <p className="text-xs uppercase tracking-[0.25em] text-slate-400">Control room</p>
            <h2 className="text-2xl font-semibold text-white">Central de performance</h2>
          </div>
          <div className="flex items-center gap-3 text-sm text-slate-400">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            Atualizando agora
          </div>
        </div>
        <motion.div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" variants={stagger}>
          {metrics.map((metric) => (
            <motion.div
              key={metric.label}
              className="rounded-2xl border border-white/10 bg-slate-950/60 p-5"
              variants={fadeUp}
              whileHover={{ y: -4 }}
            >
              <p className="text-2xl font-semibold text-white">{metric.value}</p>
              <p className="text-sm text-slate-400">{metric.label}</p>
            </motion.div>
          ))}
        </motion.div>
      </motion.div>
    </motion.section>
  );
}

export default Hero;
