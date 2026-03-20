"""
Script para re-processar produtos existentes no banco:
1. Enriquece com Gemini (gera enriched_text)
2. Re-indexa no Qdrant com os novos vetores

Uso:
    cd backend
    python reenrich_existing.py [tenant_id] [--force] [--reset-qdrant]

    --force         Re-enriquece mesmo produtos que ja tem enriched_text
    --reset-qdrant  Deleta e recria as collections do Qdrant (necessario ao trocar modelo)
    Se tenant_id for omitido, processa TODOS os tenants.
"""
import sys
from app.db.session import SessionLocal
from app.db.models import Product
from app.services.enrichment_service import EnrichmentService
from app.services.ai_service import AIService


def run(tenant_id: str = None, force: bool = False, reset_qdrant: bool = False):
    db = SessionLocal()
    try:
        query = db.query(Product)
        if tenant_id:
            query = query.filter(Product.tenant_id == tenant_id)

        products = query.all()

        if not products:
            print("Nenhum produto encontrado.")
            return

        if force:
            print("Modo --force: limpando enriched_text de todos os produtos...")
            for p in products:
                p.enriched_text = None
            db.commit()
            print("Pronto. Re-enriquecendo com o novo prompt...\n")

        tenants = {}
        for p in products:
            tenants.setdefault(p.tenant_id, []).append(p)

        for tid, tenant_products in tenants.items():
            print(f"Tenant: {tid} | {len(tenant_products)} produtos")

            # Passo 1: Enriquecer com Gemini
            EnrichmentService.enrich_and_save(tenant_products)

            # Recarrega os produtos para pegar o enriched_text salvo
            ids = [p.id for p in tenant_products]
            refreshed = db.query(Product).filter(Product.id.in_(ids)).all()

            # Passo 2: Re-indexar (com recreate se --reset-qdrant)
            collection_name = AIService.get_collection_name(tid)
            AIService.ensure_collection_exists(collection_name, force_recreate=reset_qdrant)
            AIService.generate_and_save_embeddings(products=refreshed, tenant_id=tid)
            print(f"Re-indexacao concluida para tenant {tid}.\n")

    finally:
        db.close()


if __name__ == "__main__":
    args = sys.argv[1:]
    force = "--force" in args
    reset_qdrant = "--reset-qdrant" in args
    args = [a for a in args if not a.startswith("--")]
    tid = args[0] if args else None
    run(tenant_id=tid, force=force, reset_qdrant=reset_qdrant)
