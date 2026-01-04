import { motion } from "framer-motion";
import { fadeUp } from "./animations";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "../ui/accordion";
import { Badge } from "../ui/badge";

const items = [
  {
    title: "Quais fontes posso integrar?",
    content:
      "Hoje suportamos Emarsys, GA4, Salesforce, HubSpot e VTEX, com conectores adicionais em roadmap."
  },
  {
    title: "Consigo criar dashboards customizados?",
    content:
      "Sim. Voce pode configurar KPIs, segmentos e layouts para cada time ou unidade."
  },
  {
    title: "Como funciona o AI Advisor?",
    content:
      "O advisor analisa performance e sugere playbooks com base nos dados conectados."
  },
  {
    title: "Existe suporte dedicado?",
    content:
      "Nos planos Growth e Enterprise voce tem suporte prioritario e onboarding assistido."
  }
];

function Faq() {
  return (
    <motion.section
      id="faq"
      className="mx-auto grid w-full max-w-4xl gap-8"
      variants={fadeUp}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.2 }}
    >
      <motion.div className="text-center" variants={fadeUp}>
        <Badge variant="highlight">FAQ</Badge>
        <h2 className="mt-4 text-3xl font-semibold text-white sm:text-4xl">
          Duvidas frequentes sobre a plataforma.
        </h2>
      </motion.div>

      <Accordion type="single" collapsible className="grid gap-4">
        {items.map((item) => (
          <AccordionItem key={item.title} value={item.title}>
            <AccordionTrigger>{item.title}</AccordionTrigger>
            <AccordionContent>{item.content}</AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </motion.section>
  );
}

export default Faq;
