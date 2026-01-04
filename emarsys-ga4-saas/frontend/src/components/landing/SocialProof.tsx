import { motion } from "framer-motion";
import { fadeUp, stagger } from "./animations";
import { Card } from "../ui/card";

const logos = ["RetailPro", "GrowthHub", "Atlas", "Nova", "Pulse", "Lumen"];

function SocialProof() {
  return (
    <motion.section
      id="proof"
      className="mx-auto grid w-full max-w-6xl gap-10"
      variants={fadeUp}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.2 }}
    >
      <motion.div className="grid gap-3" variants={fadeUp}>
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-cyan-300">
          Prova social
        </p>
        <h2 className="text-3xl font-semibold text-white sm:text-4xl">
          Times de marketing que ja aceleram resultados com a KeepAIS.
        </h2>
      </motion.div>

      <motion.div
        className="grid gap-4 rounded-3xl border border-white/10 bg-white/5 p-6 sm:grid-cols-3 lg:grid-cols-6"
        variants={stagger}
      >
        {logos.map((logo) => (
          <motion.div
            key={logo}
            className="flex items-center justify-center rounded-2xl border border-white/10 bg-slate-950/50 px-4 py-3 text-sm font-semibold text-slate-200"
            variants={fadeUp}
            whileHover={{ y: -4 }}
          >
            {logo}
          </motion.div>
        ))}
      </motion.div>

      <motion.div variants={fadeUp}>
        <Card className="grid gap-4">
          <p className="text-lg font-semibold text-white">
            &quot;Em menos de 30 dias reduzimos o tempo de analise em 60% e aumentamos a
            conversao das campanhas de carrinho em 24%.&quot;
          </p>
          <p className="text-sm text-slate-400">
            Diretoria de Growth, varejo omnichannel
          </p>
        </Card>
      </motion.div>
    </motion.section>
  );
}

export default SocialProof;
