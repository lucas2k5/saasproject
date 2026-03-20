import os
os.environ.setdefault("FASTEMBED_CACHE_PATH", "/app/.fastembed_cache")
from fastembed import TextEmbedding, SparseTextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.core.config import settings

# Expansão de sinônimos para melhorar o match BM25 em português
# BM25 é baseado em tokens exatos — sem isso, "calor" não matcheia "clima quente"
def _compute_category_prefixes(category) -> list:
    """
    Extrai prefixos hierárquicos de TODAS as categorias do produto (union).

    Suporta:
    - "Alimentos > Bebidas > Café"
      → ["Alimentos", "Alimentos > Bebidas", "Alimentos > Bebidas > Café"]
    - ["Alimentos > Bebidas > Café", "Alimentos > Orgânicos e Naturais"]  (múltiplos paths)
      → union de todos os prefixos
    - ["Alimentos", "Bebidas", "Café"]  (partes planas de um único path)
      → ["Alimentos", "Alimentos > Bebidas", "Alimentos > Bebidas > Café"]
    """
    if not category:
        return []

    if isinstance(category, list):
        if any(" > " in str(item) for item in category):
            paths = [str(item).strip() for item in category if item]
        else:
            paths = [" > ".join(str(p).strip() for p in category if p)]
    else:
        paths = [str(category).strip()]

    all_prefixes = set()
    for path in paths:
        parts = [p.strip() for p in path.split(" > ") if p.strip()]
        for i in range(len(parts)):
            all_prefixes.add(" > ".join(parts[:i + 1]))

    return sorted(all_prefixes)


def _get_primary_category_prefix(category, level: int):
    """
    Retorna o prefixo do nível N da categoria PRIMÁRIA (primeira da lista).
    Se o produto tiver menos níveis que o pedido, usa o mais profundo disponível.
    """
    if not category or level <= 0:
        return None

    if isinstance(category, list):
        if any(" > " in str(item) for item in category):
            primary = str(category[0]).strip()
        else:
            primary = " > ".join(str(p).strip() for p in category if p)
    else:
        primary = str(category).strip()

    parts = [p.strip() for p in primary.split(" > ") if p.strip()]
    if not parts:
        return None
    return " > ".join(parts[:level])


QUERY_EXPANSIONS = {
    "calor":   "calor quente verão temperatura quente clima quente",
    "frio":    "frio fria inverno temperatura fria gelado",
    "barato":  "barato econômico acessível promoção",
    "caro":    "caro premium luxo sofisticado",
    "verão":   "verão calor quente praia sol",
    "inverno": "inverno frio temperatura baixa aquecido",
}

def _expand_query(query: str) -> str:
    """Expande termos da query com sinônimos para melhorar o recall do BM25."""
    words = query.lower().strip().split()
    extra = []
    for word in words:
        if word in QUERY_EXPANSIONS:
            extra.append(QUERY_EXPANSIONS[word])
    if extra:
        return query + " " + " ".join(extra)
    return query

# 1. Carrega o modelo denso (semântico)
print("⏳ Carregando modelo de IA (multilingual-e5-large)...")
model = TextEmbedding(model_name="intfloat/multilingual-e5-large")
print("✅ Modelo denso carregado!")

VECTOR_SIZE = 1024  # multilingual-e5-large usa 1024 dims

# 2. Carrega o modelo esparso (BM25 para keywords)
print("⏳ Carregando modelo BM25 (sparse)...")
sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
print("✅ Modelo BM25 carregado!")

# 3. Conecta ao Qdrant
qdrant_client = QdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY or None,
)


class AIService:

    @staticmethod
    def get_collection_name(tenant_id: str):
        return f"tenant_{tenant_id.replace('-', '_')}"

    @staticmethod
    def ensure_collection_exists(collection_name: str, force_recreate: bool = False):
        """Verifica se a collection existe com config híbrida (dense + sparse). Se não, cria."""
        collections = qdrant_client.get_collections()
        exists = any(c.name == collection_name for c in collections.collections)

        if exists and force_recreate:
            print(f"Deletando collection '{collection_name}' para recriar com config híbrida...")
            qdrant_client.delete_collection(collection_name)
            exists = False

        if not exists:
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    "dense": models.VectorParams(
                        size=VECTOR_SIZE,
                        distance=models.Distance.COSINE
                    )
                },
                sparse_vectors_config={
                    "sparse": models.SparseVectorParams()
                }
            )
            print(f"Collection '{collection_name}' criada com vetores densos ({VECTOR_SIZE} dims) + BM25 sparse.")

        # Garante índices de payload (idempotente — seguro chamar sempre)
        qdrant_client.create_payload_index(
            collection_name=collection_name,
            field_name="tenant_id",
            field_schema="keyword",
        )
        qdrant_client.create_payload_index(
            collection_name=collection_name,
            field_name="category_prefixes",
            field_schema="keyword",
        )

    @staticmethod
    def generate_and_save_embeddings(products: list, tenant_id: str):
        """
        Gera vetores densos (e5-large) + esparsos (BM25) e salva no Qdrant.
        """
        try:
            collection_name = AIService.get_collection_name(tenant_id)
            AIService.ensure_collection_exists(collection_name)

            texts = []
            for p in products:
                if getattr(p, 'enriched_text', None):
                    raw = f"{p.name}. {p.enriched_text}"
                else:
                    brand = p.attributes.get('brand', '') if p.attributes else ''
                    raw = f"{p.name}. {p.description}. Marca: {brand}. Categoria: {p.category}"
                texts.append(f"passage: {raw}")

            print(f"🧠 Vetorizando {len(texts)} produtos para o Tenant {tenant_id}...")

            # Vetores densos (semânticos)
            dense_embeddings = list(model.embed(texts))

            # Vetores esparsos (BM25 keywords)
            sparse_embeddings = list(sparse_model.embed(texts))

            # Upsert com ambos os vetores
            points = []
            for i, product in enumerate(products):
                payload = {
                    "product_id": str(product.id),
                    "external_id": product.external_id,
                    "name": product.name,
                    "price": product.price,
                    "category": product.category,
                    "image_url": product.image_url,
                    "attributes": product.attributes,
                    "enriched_text": getattr(product, "enriched_text", None),
                    "tenant_id": tenant_id,
                    "category_prefixes": _compute_category_prefixes(product.category),
                }

                sparse_vec = sparse_embeddings[i]
                point = models.PointStruct(
                    id=str(product.id),
                    vector={
                        "dense": dense_embeddings[i].tolist(),
                        "sparse": models.SparseVector(
                            indices=sparse_vec.indices.tolist(),
                            values=sparse_vec.values.tolist()
                        )
                    },
                    payload=payload
                )
                points.append(point)

            qdrant_client.upsert(
                collection_name=collection_name,
                points=points
            )
            print(f"✅ Sucesso: {len(points)} vetores híbridos indexados.")

        except Exception as e:
            print(f"❌ Erro Crítico na Vetorização: {e}")

    @staticmethod
    def search(query: str, tenant_id: str, limit: int = 10):
        """
        Busca Híbrida Inteligente:
        1. Tenta match EXATO pelo SKU.
        2. Preenche o resto com busca HÍBRIDA (Dense semântico + BM25 keywords via RRF Fusion).
        """
        collection_name = AIService.get_collection_name(tenant_id)
        results = []
        exclude_ids = []

        # --- FASE 1: Busca Exata por SKU ---
        try:
            exact_matches, _ = qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="external_id",
                            match=models.MatchValue(value=query)
                        )
                    ]
                ),
                limit=1,
                with_payload=True
            )

            if exact_matches:
                print(f"🎯 Match exato encontrado para SKU: {query}")
                match = exact_matches[0]
                results.append({
                    "score": 1.0,
                    "product": match.payload
                })
                exclude_ids.append(match.id)

        except Exception as e:
            print(f"Erro na busca exata: {e}")

        # --- FASE 2: Busca Híbrida (Dense + BM25 com RRF Fusion) ---
        limit_vector = limit - len(results)
        if limit_vector <= 0:
            return results

        try:
            # Vetor denso para semântica
            query_dense = list(model.embed([f"query: {query}"]))[0].tolist()

            # Vetor esparso para keywords (BM25 com expansão de sinônimos)
            query_sparse_raw = list(sparse_model.embed([_expand_query(query)]))[0]
            query_sparse = models.SparseVector(
                indices=query_sparse_raw.indices.tolist(),
                values=query_sparse_raw.values.tolist()
            )

            # Filtro de exclusão do SKU exato (se encontrado)
            search_filter = None
            if exclude_ids:
                search_filter = models.Filter(
                    must_not=[models.HasIdCondition(has_id=exclude_ids)]
                )

            # Prefetch amplo de cada índice + fusão RRF para reranking
            prefetch_limit = limit_vector * 3

            search_result = qdrant_client.query_points(
                collection_name=collection_name,
                prefetch=[
                    models.Prefetch(
                        query=query_dense,
                        using="dense",
                        limit=prefetch_limit,
                        filter=search_filter
                    ),
                    models.Prefetch(
                        query=query_sparse,
                        using="sparse",
                        limit=prefetch_limit,
                        filter=search_filter
                    ),
                ],
                query=models.FusionQuery(fusion=models.Fusion.DBSF),
                limit=limit_vector,
                with_payload=True
            ).points

            for hit in search_result:
                results.append({
                    "score": hit.score,
                    "product": hit.payload
                })

            return results

        except Exception as e:
            print(f"Aviso de busca híbrida: {e}")
            return results

    @staticmethod
    def recommend(product_id: str, tenant_id: str, limit: int, price_low: float, price_high: float, similarity: float, category_level: int = 0):
        """
        Gera recomendações por similaridade usando vetor denso como âncora.
        """
        print(f"\n[DEBUG] Iniciando recomendação para product_id: {product_id} | tenant_id: {tenant_id}")
        collection_name = AIService.get_collection_name(tenant_id)

        try:
            # 1. Recuperar o Produto de Referência
            points = qdrant_client.retrieve(
                collection_name=collection_name,
                ids=[product_id],
                with_payload=True
            )

            if not points:
                print(f"[DEBUG] Produto {product_id} não encontrado no Qdrant.")
                return None

            ref_product = points[0]
            ref_price = float(ref_product.payload['price'])
            print(f"[DEBUG] Produto de referência: {ref_product.payload['name']} | Preço: {ref_price}")

            # 2. Busca vizinhos usando vetor denso como âncora (recomendação é semântica, não keyword)
            print(f"[DEBUG] Buscando vizinhos com similaridade > {similarity} e tenant_id = {tenant_id}")

            # Filtro de tenant obrigatório + filtro de categoria por nível (opcional)
            filter_conditions = [
                models.FieldCondition(
                    key="tenant_id",
                    match=models.MatchValue(value=tenant_id)
                )
            ]

            if category_level > 0:
                target_prefix = _get_primary_category_prefix(
                    ref_product.payload.get("category"), category_level
                )
                if target_prefix:
                    print(f"[DEBUG] Filtro de categoria nível {category_level}: '{target_prefix}'")
                    filter_conditions.append(
                        models.FieldCondition(
                            key="category_prefixes",
                            match=models.MatchAny(any=[target_prefix])
                        )
                    )
                else:
                    print(f"[DEBUG] category_level={category_level} mas produto sem categoria definida. Sem filtro.")

            search_result = qdrant_client.query_points(
                collection_name=collection_name,
                query=ref_product.id,
                using="dense",
                limit=limit,
                score_threshold=similarity,
                with_payload=True,
                query_filter=models.Filter(must=filter_conditions)
            ).points

            print(f"[DEBUG] Qdrant retornou {len(search_result)} pontos.")
            if not search_result:
                print("[DEBUG] A busca não retornou resultados. Possíveis causas:")
                print("  1. Dados sem reindexação híbrida. Rode: python reenrich_existing.py --reset-qdrant")
                print("  2. O threshold de similaridade pode estar muito alto.")
                print("  3. Não existem produtos similares suficientes.")

            # 3. Classificação por faixa de preço
            recommendations = {
                "cheaper": [],
                "similar": [],
                "expensive": []
            }

            for hit in search_result:
                prod = hit.payload
                price = float(prod['price'])

                item = {
                    "score": hit.score,
                    "id": prod['external_id'],
                    "product_id": prod['product_id'],
                    "name": prod['name'],
                    "price": price,
                    "image": prod['image_url'],
                    "category": prod['category'],
                    "attributes": prod['attributes']
                }

                if price < (ref_price * price_low):
                    recommendations["cheaper"].append(item)
                elif price > (ref_price * price_high):
                    recommendations["expensive"].append(item)
                else:
                    recommendations["similar"].append(item)

            return {
                "reference": {
                    "id": ref_product.payload['external_id'],
                    "name": ref_product.payload['name'],
                    "price": ref_price,
                    "category": ref_product.payload['category']
                },
                "recommendations": recommendations
            }

        except Exception as e:
            print(f"Erro ao gerar recomendação: {e}")
            return None

    @staticmethod
    def compute_and_save_similars(tenant_id: str, top_n: int = 50):
        """
        Pre-computa os top N produtos similares para cada produto do tenant.
        Grava na tabela product_similars para uso no job noturno de recomendacao
        (evita chamadas ao Qdrant no processamento batch).
        """
        from app.db.session import SessionLocal
        from app.db.models import Product, ProductSimilar
        import uuid as uuid_mod

        collection_name = AIService.get_collection_name(tenant_id)

        db = SessionLocal()
        try:
            # Carrega todos os produtos ativos com preco
            products = db.query(Product).filter(
                Product.tenant_id == tenant_id,
                Product.is_active == True
            ).all()

            if not products:
                print("Nenhum produto ativo para computar similares.")
                return

            product_map = {str(p.id): p for p in products}
            product_ids = list(product_map.keys())

            print(f"Computando top {top_n} similares para {len(products)} produtos...")

            # Limpa similares antigos do tenant
            db.query(ProductSimilar).filter(
                ProductSimilar.tenant_id == tenant_id
            ).delete(synchronize_session=False)
            db.flush()

            # Processa em batches para nao sobrecarregar o Qdrant
            BATCH = 50
            total_saved = 0

            for batch_start in range(0, len(product_ids), BATCH):
                batch_ids = product_ids[batch_start:batch_start + BATCH]
                similars_to_insert = []

                for pid in batch_ids:
                    ref_product = product_map[pid]
                    ref_price = ref_product.price or 0

                    try:
                        search_result = qdrant_client.query_points(
                            collection_name=collection_name,
                            query=pid,
                            using="dense",
                            limit=top_n,
                            score_threshold=0.3,
                            with_payload=["product_id", "price"],
                            query_filter=models.Filter(must=[
                                models.FieldCondition(
                                    key="tenant_id",
                                    match=models.MatchValue(value=tenant_id)
                                )
                            ])
                        ).points
                    except Exception as e:
                        print(f"  Erro ao buscar similares para {pid}: {e}")
                        continue

                    for rank_idx, hit in enumerate(search_result):
                        sim_pid = hit.payload.get("product_id", str(hit.id))
                        if sim_pid == pid:
                            continue

                        sim_price = hit.payload.get("price", 0) or 0
                        price_ratio = (sim_price / ref_price) if ref_price > 0 else None

                        similars_to_insert.append({
                            "id": uuid_mod.uuid4(),
                            "tenant_id": tenant_id,
                            "product_id": pid,
                            "similar_product_id": sim_pid,
                            "rank": rank_idx + 1,
                            "score": round(hit.score, 4),
                            "price_ratio": round(price_ratio, 4) if price_ratio is not None else None,
                        })

                if similars_to_insert:
                    db.bulk_insert_mappings(ProductSimilar, similars_to_insert)
                    total_saved += len(similars_to_insert)

                lote = batch_start // BATCH + 1
                total_lotes = (len(product_ids) + BATCH - 1) // BATCH
                print(f"  Lote {lote}/{total_lotes}: {len(similars_to_insert)} similares computados.")

            db.commit()
            print(f"ProductSimilars: {total_saved} registros salvos para tenant {tenant_id}.")

        except Exception as e:
            db.rollback()
            print(f"Erro ao computar similares: {e}")
        finally:
            db.close()

    @staticmethod
    def get_collection_info(tenant_id: str = "default"):
        try:
            collection_name = AIService.get_collection_name(tenant_id)
            info = qdrant_client.count(collection_name=collection_name, exact=True)
            return {"points_count": info.count, "status": "green"}
        except Exception as e:
            print(f"Qdrant Error: {e}")
            return {"points_count": 0}
