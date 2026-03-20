import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { BrainCircuit, ShoppingCart, TrendingUp, Users, Percent, Package } from "lucide-react";
import { fadeUp, stagger } from "./animations";
import { Button } from "../ui/button";

const highlights = [
  {
    icon: BrainCircuit,
    title: "IA Generativa",
    description: "Embeddings vetoriais geram recomendações personalizadas com base no comportamento real do cliente.",
  },
  {
    icon: ShoppingCart,
    title: "Pedidos & Ofertas",
    description: "Importe catálogo, pedidos e ofertas para alimentar o motor de recomendação automaticamente.",
  },
  {
    icon: TrendingUp,
    title: "Ciclo de Vida",
    description: "Segmentação RFV automática identifica clientes ativos, em risco e inativos.",
  },
  {
    icon: Users,
    title: "Customer Intelligence",
    description: "Visão 360 do cliente com histórico de compras, ticket médio e frequência.",
  },
  {
    icon: Percent,
    title: "Ofertas Inteligentes",
    description: "Monte promoções segmentadas por canal, loja e público-alvo com priorização automática.",
  },
  {
    icon: Package,
    title: "Catálogo Vetorizado",
    description: "Busca semântica por produtos similares usando embeddings multilíngues de última geração.",
  },
];

function RecommenderShowcase() {
  return (
    <motion.section
      id="recommender"
      className="mx-auto grid w-full max-w-6xl gap-14"
      variants={fadeUp}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.15 }}
    >
      {/* Header */}
      <motion.div className="mx-auto grid max-w-3xl gap-5 text-center" variants={fadeUp}>
        <div className="mx-auto flex items-center gap-2 rounded-full border border-orange-500/30 bg-orange-500/10 px-4 py-1.5">
          <BrainCircuit className="h-4 w-4 text-orange-400" />
          <span className="text-xs font-semibold uppercase tracking-[0.2em] text-orange-400">
            Novo produto
          </span>
        </div>
        <h2 className="text-3xl font-semibold text-white sm:text-4xl">
          Recomendador de Produtos{" "}
          <span className="bg-gradient-to-r from-orange-400 to-amber-300 bg-clip-text text-transparent">
            com IA
          </span>
        </h2>
        <p className="text-base text-slate-300 sm:text-lg">
          Motor de recomendação inteligente integrado ao KeepAIS. Importe seu catálogo,
          conecte pedidos e deixe a IA encontrar os produtos certos para cada cliente
          &mdash; tudo em tempo real.
        </p>
      </motion.div>

      {/* Visual card */}
      <motion.div
        className="rounded-3xl border border-white/10 bg-gradient-to-br from-slate-950/80 to-slate-900/60 p-8 shadow-[0_30px_60px_rgba(7,11,24,0.4)] sm:p-10"
        variants={fadeUp}
      >
        <div className="grid gap-10 lg:grid-cols-2 lg:items-center">
          {/* Left — description */}
          <div className="grid gap-6">
            <div className="inline-flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-orange-400 animate-pulse" />
              <span className="text-xs font-semibold uppercase tracking-[0.25em] text-slate-400">
                RecomendAI Engine
              </span>
            </div>
            <h3 className="text-2xl font-semibold text-white sm:text-3xl">
              Do catálogo ao insight em minutos
            </h3>
            <p className="text-slate-300">
              Faça upload de CSVs com produtos, clientes e pedidos. O motor vetoriza tudo,
              calcula similaridade e gera recomendações personalizadas por cliente, canal e loja.
            </p>
            <div className="grid grid-cols-3 gap-4">
              <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-4 text-center">
                <p className="text-2xl font-semibold text-orange-400">150+</p>
                <p className="text-xs text-slate-400">Produtos indexados</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-4 text-center">
                <p className="text-2xl font-semibold text-cyan-400">80+</p>
                <p className="text-xs text-slate-400">Clientes analisados</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-4 text-center">
                <p className="text-2xl font-semibold text-emerald-400">2.2k+</p>
                <p className="text-xs text-slate-400">Pedidos processados</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-3 pt-2">
              <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                <Button asChild size="lg">
                  <Link to="/dashboard/recommendations">Experimentar agora</Link>
                </Button>
              </motion.div>
              <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
                <Button variant="outline" size="lg" asChild>
                  <a href="#pricing">Ver planos</a>
                </Button>
              </motion.div>
            </div>
          </div>

          {/* Right — feature grid */}
          <motion.div className="grid gap-3 sm:grid-cols-2" variants={stagger}>
            {highlights.map((item) => {
              const Icon = item.icon;
              return (
                <motion.div
                  key={item.title}
                  className="rounded-2xl border border-white/10 bg-slate-950/60 p-5 transition-colors hover:border-orange-500/30"
                  variants={fadeUp}
                  whileHover={{ y: -4 }}
                >
                  <Icon className="mb-3 h-5 w-5 text-orange-400" />
                  <p className="text-sm font-semibold text-white">{item.title}</p>
                  <p className="mt-1 text-xs leading-relaxed text-slate-400">
                    {item.description}
                  </p>
                </motion.div>
              );
            })}
          </motion.div>
        </div>
      </motion.div>
    </motion.section>
  );
}

export default RecommenderShowcase;
