import json
import re
import google.generativeai as genai
from app.core.config import settings
from app.db.session import SessionLocal

BATCH_SIZE = 20

genai.configure(api_key=settings.GEMINI_API_KEY)
_gemini_model = genai.GenerativeModel("gemini-2.5-flash-lite")


class EnrichmentService:

    @staticmethod
    def enrich_and_save(products: list):
        """
        Enriquece produtos sem enriched_text usando Gemini e salva no banco.
        Abre sua propria sessao de DB (seguro para uso em background tasks).
        """
        to_enrich = [p for p in products if not p.enriched_text]

        if not to_enrich:
            print("Todos os produtos ja possuem enriched_text. Nada a fazer.")
            return

        print(f"Enriquecendo {len(to_enrich)} produtos com Gemini...")

        db = SessionLocal()
        try:
            for i in range(0, len(to_enrich), BATCH_SIZE):
                batch = to_enrich[i:i + BATCH_SIZE]
                lote_num = i // BATCH_SIZE + 1
                enriched_texts = EnrichmentService._call_gemini(batch)

                saved = 0
                failed = 0
                for product, text in zip(batch, enriched_texts):
                    if text:
                        db.query(type(product)).filter(
                            type(product).id == product.id
                        ).update({"enriched_text": text})
                        product.enriched_text = text  # atualiza em memória para generate_and_save_embeddings usar
                        saved += 1
                    else:
                        failed += 1

                db.commit()

                if failed == 0:
                    print(f"  Lote {lote_num}: {saved} produtos enriquecidos.")
                else:
                    print(f"  Lote {lote_num}: {saved} enriquecidos, {failed} falharam (serao reprocessados na proxima execucao).")

        except Exception as e:
            db.rollback()
            print(f"Erro critico ao salvar enriched_text: {e}")
        finally:
            db.close()

    @staticmethod
    def _call_gemini(products: list) -> list:
        """
        Envia um batch de produtos para o Gemini e retorna lista de textos enriquecidos.
        Em caso de falha, retorna strings vazias para nao bloquear o pipeline.
        """
        products_data = []
        for p in products:
            products_data.append({
                "name": p.name or "",
                "description": p.description or "",
                "category": str(p.category or ""),
                "attributes": p.attributes or {}
            })

        prompt = f"""Voce e um especialista em SEO e busca de e-commerce brasileiro. Sua tarefa e gerar textos de produtos otimizados para busca — o objetivo e que quando um comprador digitar uma palavra no campo de busca, o produto certo apareca.

REGRA PRINCIPAL: O texto deve conter as palavras EXATAS que um comprador brasileiro digitaria para encontrar esse produto. Nao use sinonimos rebuscados — use o vocabulario natural de busca.

Para cada produto abaixo, gere um texto em portugues que:

1. Use os atributos do produto para diferenciar — resolucao, tamanho, tecnologia, material, cor, sabor, composicao, etc.

2. Contenha obrigatoriamente as palavras-chave de busca mais obvias. Pense em DUAS dimensoes:
   a) O QUE o produto e: suas propriedades, ingredientes ativos, especificacoes tecnicas, composicao
   b) POR QUE alguem compra: beneficios, efeitos, resultados esperados, problema que resolve

   Exemplos de como pensar:
   - Cha verde: comprador digita "antioxidante", "cafeina", "emagrecer", "termogenico", "digestao", "energia" — o texto DEVE conter essas propriedades especificas, nao apenas "para o cafe da manha"
   - Proteina em po: "ganho de massa", "musculo", "pos-treino", "whey", "aminoacidos"
   - Roupa de verao: "calor", "verao", "leve", "fresco", "praia" — o texto DEVE conter essas palavras
   - Roupa de frio: "frio", "inverno", "quente", "aquece", "casaco" — o texto DEVE conter essas palavras
   - TV: "4K", "smart", "OLED", "HDR", "Netflix" — mantenha os termos tecnicos
   - Eletrodomestico: funcao principal, capacidade, diferenciais praticos
   - Aplique essa logica para qualquer categoria: o texto deve responder tanto "o que e?" quanto "para que serve / por que comprar?"

3. Se a descricao do produto for generica ou pouco informativa (ex: "Ideal para o dia a dia", "Produto convencional", "Armazenar em local fresco"), IGNORE-A completamente. Use o NOME do produto como fonte primaria — ele geralmente contem o tipo exato do produto, suficiente para voce descrever suas propriedades reais. Exemplos:
   - Nome "Cha Verde 3 Coracoes 250g" → voce sabe que cha verde tem cafeina suave, antioxidantes, flavonoides, propriedades termogenicas, auxilia na digestao e no emagrecimento — use isso
   - Nome "Biscoito Recheado Chocolate Bauducco 130g" → voce sabe que e um biscoito doce, crocante, recheio cremoso de chocolate — use isso
   - Nome "Arroz Branco Tipo 1 Camil 5kg" → voce sabe que e um grao branco, cozimento rapido, acompanhamento para feijao e proteinas — use isso

4. NUNCA use uma palavra de forma ambigua. Nao use "calor" para descrever o aquecimento de um casaco — isso confunde a busca. Use "mantém aquecido" ou "protecao contra o frio".

5. NUNCA gere texto de marketing generico como "perfeito para o seu dia a dia" sem antes ter descrito as propriedades reais do produto.

6. OBRIGATORIO: cada texto deve ter NO MINIMO 2 sentencas e NO MAXIMO 4 sentencas. Uma unica sentenca e considerada falha e sera rejeitada. Estrutura esperada:
   - Sentenca 1: O QUE e o produto e suas especificacoes/composicao principais
   - Sentenca 2: PARA QUE serve / que problema resolve / beneficios principais
   - Sentenca 3 (se aplicavel): Diferenciais de uso, como usar, ocasioes ideais
   - Sentenca 4 (se aplicavel): Palavras-chave adicionais de busca que ainda nao foram mencionadas

Retorne APENAS um JSON array com exatamente {len(products)} strings, uma por produto, na mesma ordem.
Sem markdown, sem explicacoes, apenas o JSON array.

Produtos:
{json.dumps(products_data, ensure_ascii=False, indent=2)}"""

        try:
            response = _gemini_model.generate_content(prompt)
            raw = response.text.strip()

            # Remove markdown code block se o modelo retornar ```json ... ```
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

            texts = json.loads(raw)

            if isinstance(texts, list) and len(texts) == len(products):
                return texts

            print(f"Gemini retornou {len(texts)} itens, esperado {len(products)}. Usando fallback.")
        except Exception as e:
            print(f"Erro na chamada Gemini: {e}")

        # Fallback: retorna None por produto, o AIService usara o texto original
        # e o produto ficara com enriched_text=None para ser reprocessado depois
        return [None] * len(products)
