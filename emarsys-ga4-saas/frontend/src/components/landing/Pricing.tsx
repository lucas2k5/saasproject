import { motion } from "framer-motion";
import { fadeUp, stagger } from "./animations";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

const plans = [
  {
    title: "Starter",
    price: "R$ 1.490",
    description: "Ideal para operar uma unica unidade.",
    features: [
      "1 integracao principal",
      "Dashboards essenciais",
      "Ate 1.000 eventos por mes",
      "Suporte por email"
    ]
  },
  {
    title: "Growth",
    price: "R$ 3.900",
    description: "Para times com necessidades avancadas.",
    features: [
      "Emarsys + GA4 integrados",
      "Todos os modulos ativos",
      "Ate 50.000 eventos por mes",
      "AI Advisor incluso",
      "Suporte prioritario"
    ],
    highlight: true
  },
  {
    title: "Enterprise",
    price: "Sob consulta",
    description: "Operacoes complexas e multiplas unidades.",
    features: [
      "Eventos ilimitados",
      "Multiplas contas",
      "SLA garantido",
      "Onboarding dedicado"
    ]
  }
];

function Pricing() {
  return (
    <motion.section
      id="pricing"
      className="mx-auto grid w-full max-w-6xl gap-10"
      variants={fadeUp}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.2 }}
    >
      <motion.div className="text-center" variants={fadeUp}>
        <Badge variant="highlight">Planos</Badge>
        <h2 className="mt-4 text-3xl font-semibold text-white sm:text-4xl">
          Planos que acompanham o ritmo do seu time.
        </h2>
        <p className="mt-3 text-base text-slate-300">
          Combine recursos, automacoes e nivel de suporte de acordo com o seu objetivo.
        </p>
      </motion.div>

      <motion.div className="grid gap-6 lg:grid-cols-3" variants={stagger}>
        {plans.map((plan) => (
          <motion.div
            key={plan.title}
            variants={fadeUp}
            whileHover={{ y: -6 }}
            transition={{ duration: 0.2 }}
          >
            <Card
              className={
                plan.highlight
                  ? "border-orange-400/40 bg-orange-500/10 shadow-[0_30px_60px_rgba(249,115,22,0.25)]"
                  : ""
              }
            >
              <CardHeader className="gap-3">
                {plan.highlight && <Badge variant="highlight">Mais popular</Badge>}
                <CardTitle className="text-2xl">{plan.title}</CardTitle>
                <p className="text-3xl font-semibold text-white">{plan.price}</p>
                <p className="text-sm text-slate-300">{plan.description}</p>
              </CardHeader>
              <CardContent>
                <ul className="grid gap-3 text-sm text-slate-300">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-orange-400" />
                      {feature}
                    </li>
                  ))}
                </ul>
                <Button className="mt-6 w-full" variant={plan.highlight ? "default" : "outline"}>
                  Escolher plano
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </motion.div>
    </motion.section>
  );
}

export default Pricing;
