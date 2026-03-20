import hashlib
import json
import uuid
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.db.models import Product, Category

BATCH_LIMIT = 1000


def _compute_hash(name: str, description: str, attributes: dict, category: list) -> str:
    """Hash dos campos relevantes para detectar mudanças e evitar re-enrichment desnecessário."""
    raw = json.dumps({
        "name": name,
        "description": description,
        "attributes": attributes,
        "category": category,
    }, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(raw.encode()).hexdigest()


class IngestionService:

    @staticmethod
    def upsert_products_batch(items: list[dict], tenant_id: str, db: Session) -> dict:
        """
        Faz upsert de até BATCH_LIMIT produtos.
        Retorna dict com contadores: created, updated, unchanged, to_enrich (lista de Product).
        """
        if len(items) > BATCH_LIMIT:
            raise ValueError(f"Limite de {BATCH_LIMIT} produtos por chamada excedido.")

        # Carrega hashes existentes em memória (1 query só)
        external_ids = [str(i.get("external_id", "")) for i in items]
        existing = db.query(Product.external_id, Product.data_hash, Product.id).filter(
            Product.tenant_id == tenant_id,
            Product.external_id.in_(external_ids)
        ).all()
        existing_map = {row.external_id: {"hash": row.data_hash, "id": row.id} for row in existing}

        products_to_upsert = []
        categories_batch: dict[str, Any] = {}
        unchanged_ids = set()

        for item in items:
            ext_id = str(item.get("external_id", "")).strip()
            if not ext_id:
                continue

            name = str(item.get("name") or "Sem Nome")
            description = str(item.get("description") or "")
            price_raw = item.get("price")
            price = float(price_raw) if price_raw is not None else None
            image_url = str(item.get("image_url") or "")
            attributes = item.get("attributes") or {}
            if not isinstance(attributes, dict):
                attributes = {}

            # Normaliza categoria
            raw_cat = item.get("category", [])
            if isinstance(raw_cat, str):
                try:
                    parsed = json.loads(raw_cat.replace("'", '"'))
                    category = parsed if isinstance(parsed, list) else [raw_cat]
                except Exception:
                    category = [raw_cat]
            elif isinstance(raw_cat, list):
                category = raw_cat
            else:
                category = []

            new_hash = _compute_hash(name, description, attributes, category)
            current = existing_map.get(ext_id)

            # Se hash idêntico → não precisa re-enriquecer nem re-embedar
            if current and current["hash"] == new_hash:
                unchanged_ids.add(ext_id)
                continue

            # Prepara categorias
            for path in category:
                if not path:
                    continue
                parts = [p.strip() for p in str(path).split(">")]
                cur_path = ""
                for i, part in enumerate(parts):
                    parent = cur_path if cur_path else None
                    cur_path = f"{cur_path} > {part}" if cur_path else part
                    if cur_path not in categories_batch:
                        categories_batch[cur_path] = {
                            "tenant_id": tenant_id,
                            "path": cur_path,
                            "name": part,
                            "level": i,
                            "parent_path": parent,
                        }

            products_to_upsert.append({
                "id": current["id"] if current else str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "external_id": ext_id,
                "name": name,
                "price": price,
                "description": description,
                "image_url": image_url,
                "category": category,
                "attributes": attributes,
                "data_hash": new_hash,
                "is_active": item.get("is_active", True),
                # Zera enriched_text para forçar re-enrichment quando dados mudaram
                "enriched_text": None,
            })

        # Upsert categorias
        if categories_batch:
            stmt = pg_insert(Category).values(list(categories_batch.values()))
            stmt = stmt.on_conflict_do_nothing(constraint='uq_category_tenant_path')
            db.execute(stmt)

        # Upsert produtos
        created = 0
        updated = 0
        if products_to_upsert:
            new_ext_ids = {p["external_id"] for p in products_to_upsert}
            created = len(new_ext_ids - set(existing_map.keys()))
            updated = len(new_ext_ids & set(existing_map.keys()))

            stmt = pg_insert(Product).values(products_to_upsert)
            stmt = stmt.on_conflict_do_update(
                constraint='uq_product_tenant_extid',
                set_={
                    "name": stmt.excluded.name,
                    "price": stmt.excluded.price,
                    "description": stmt.excluded.description,
                    "image_url": stmt.excluded.image_url,
                    "category": stmt.excluded.category,
                    "attributes": stmt.excluded.attributes,
                    "data_hash": stmt.excluded.data_hash,
                    "is_active": stmt.excluded.is_active,
                    "enriched_text": stmt.excluded.enriched_text,
                }
            )
            db.execute(stmt)

        db.commit()

        # Recarrega os produtos que precisam de enriquecimento
        to_enrich = []
        if products_to_upsert:
            upserted_ext_ids = [p["external_id"] for p in products_to_upsert]
            to_enrich = db.query(Product).filter(
                Product.tenant_id == tenant_id,
                Product.external_id.in_(upserted_ext_ids)
            ).all()

        return {
            "created": created,
            "updated": updated,
            "unchanged": len(unchanged_ids),
            "errors": [],
            "to_enrich": to_enrich,
        }
