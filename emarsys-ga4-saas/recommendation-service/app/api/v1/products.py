from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from uuid import UUID

from app.db.session import get_db
from app.api.deps import get_current_user
from app.db.models import User, Product, Category, ProductPrice, ProductStock, Channel, Store
from app.services.ingestion_service import IngestionService, BATCH_LIMIT
from app.services.ai_service import AIService
from app.services.enrichment_service import EnrichmentService
from app.schemas.product import ProductResponse, ProductDetailResponse

router = APIRouter()

BATCH_RESPONSE_LIMIT = 1000


def _enrich_and_embed(products: list, tenant_id: str, compute_similars: bool = False):
    EnrichmentService.enrich_and_save(products)
    AIService.generate_and_save_embeddings(products=products, tenant_id=tenant_id)
    if compute_similars:
        AIService.compute_and_save_similars(tenant_id=tenant_id)


# ------------------------------------------------------------------ #
# Schemas
# ------------------------------------------------------------------ #

class ProductBatchItem(BaseModel):
    external_id: str
    name: str
    price: Optional[float] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    category: List[str] = []
    attributes: Dict[str, Any] = {}
    is_active: bool = True


class ProductBatchRequest(BaseModel):
    items: List[ProductBatchItem]


class ProductPatchItem(BaseModel):
    external_id: str
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[List[str]] = None
    attributes: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ProductPatchRequest(BaseModel):
    items: List[ProductPatchItem]


class ProductDeleteRequest(BaseModel):
    external_ids: List[str]


class BatchResponse(BaseModel):
    created: int
    updated: int
    unchanged: int
    errors: List[str] = []


# ------------------------------------------------------------------ #
# GET
# ------------------------------------------------------------------ #

@router.get("/", response_model=List[ProductResponse])
def list_products(
    q: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if limit > BATCH_RESPONSE_LIMIT:
        raise HTTPException(422, f"limit máximo é {BATCH_RESPONSE_LIMIT}")

    limit = min(limit, 200)
    query = db.query(Product).filter(Product.tenant_id == current_user.tenant_id)
    if q:
        safe_q = q.replace("%", r"\%").replace("_", r"\_")
        query = query.filter(Product.name.ilike(f"%{safe_q}%", escape="\\"))
    if category:
        cat_str = cast(Product.category, String)
        query = query.filter(or_(
            cat_str.ilike(f'%"{category}"%'),
            cat_str.ilike(f'%"{category} >%')
        ))
    return query.offset(skip).limit(limit).all()


@router.get("/categories/tree")
def get_category_tree(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cats = db.query(Category).filter(Category.tenant_id == current_user.tenant_id).all()
    tree = {}
    for c in cats:
        parts = [p.strip() for p in c.path.split(">")]
        curr = tree
        for part in parts:
            if part not in curr:
                curr[part] = {}
            curr = curr[part]

    def build(node, parent=""):
        res = []
        for k in sorted(node.keys()):
            path = f"{parent} > {k}" if parent else k
            res.append({"label": k, "value": path, "children": build(node[k], path)})
        return res

    return build(tree)


@router.get("/{product_id}/prices-stock")
def get_product_prices_stock(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tenant_id = current_user.tenant_id

    product = None
    try:
        uuid_obj = UUID(product_id)
        product = db.query(Product).filter(
            Product.id == uuid_obj,
            Product.tenant_id == tenant_id
        ).first()
    except ValueError:
        pass

    if not product:
        product = db.query(Product).filter(
            Product.external_id == product_id,
            Product.tenant_id == tenant_id
        ).first()

    if not product:
        raise HTTPException(404, "Produto não encontrado")

    prices_rows = (
        db.query(
            ProductPrice.price,
            Channel.channel_id.label("channel_ext_id"),
            Channel.name.label("channel_name"),
            Store.store_id.label("store_ext_id"),
            Store.name.label("store_name"),
        )
        .join(Channel, ProductPrice.channel_id == Channel.id)
        .join(Store, ProductPrice.store_id == Store.id)
        .filter(ProductPrice.product_id == product.id)
        .all()
    )

    stock_rows = (
        db.query(
            ProductStock.quantity,
            ProductStock.available,
            Channel.channel_id.label("channel_ext_id"),
            Channel.name.label("channel_name"),
            Store.store_id.label("store_ext_id"),
            Store.name.label("store_name"),
        )
        .join(Channel, ProductStock.channel_id == Channel.id)
        .join(Store, ProductStock.store_id == Store.id)
        .filter(ProductStock.product_id == product.id)
        .all()
    )

    return {
        "prices": [
            {
                "channel_id": r.channel_ext_id,
                "channel_name": r.channel_name,
                "store_id": r.store_ext_id,
                "store_name": r.store_name,
                "price": r.price,
            }
            for r in prices_rows
        ],
        "stock": [
            {
                "channel_id": r.channel_ext_id,
                "channel_name": r.channel_name,
                "store_id": r.store_ext_id,
                "store_name": r.store_name,
                "quantity": r.quantity,
                "available": r.available,
            }
            for r in stock_rows
        ],
    }


@router.get("/{product_id}", response_model=ProductDetailResponse)
def get_product_detail(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    product = None
    try:
        uuid_obj = UUID(product_id)
        product = db.query(Product).filter(
            Product.id == uuid_obj,
            Product.tenant_id == current_user.tenant_id
        ).first()
    except ValueError:
        pass

    if not product:
        product = db.query(Product).filter(
            Product.external_id == product_id,
            Product.tenant_id == current_user.tenant_id
        ).first()

    if not product:
        raise HTTPException(404, "Produto não encontrado")
    return product


# ------------------------------------------------------------------ #
# POST /batch  (upsert inteligente)
# ------------------------------------------------------------------ #

@router.post("/batch", response_model=BatchResponse)
def upsert_products_batch(
    body: ProductBatchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if len(body.items) > BATCH_LIMIT:
        raise HTTPException(422, f"Máximo de {BATCH_LIMIT} produtos por chamada.")

    items = [i.model_dump() for i in body.items]
    result = IngestionService.upsert_products_batch(items, current_user.tenant_id, db)

    if result["to_enrich"]:
        background_tasks.add_task(
            _enrich_and_embed,
            products=result["to_enrich"],
            tenant_id=current_user.tenant_id
        )

    return BatchResponse(
        created=result["created"],
        updated=result["updated"],
        unchanged=result["unchanged"],
        errors=result["errors"],
    )


# ------------------------------------------------------------------ #
# PATCH /batch  (atualização parcial)
# ------------------------------------------------------------------ #

@router.patch("/batch", response_model=BatchResponse)
def patch_products_batch(
    body: ProductPatchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if len(body.items) > BATCH_LIMIT:
        raise HTTPException(422, f"Máximo de {BATCH_LIMIT} produtos por chamada.")

    external_ids = [i.external_id for i in body.items]
    existing = db.query(Product).filter(
        Product.tenant_id == current_user.tenant_id,
        Product.external_id.in_(external_ids)
    ).all()
    existing_map = {p.external_id: p for p in existing}

    updated = 0
    to_enrich = []
    errors = []

    for item in body.items:
        product = existing_map.get(item.external_id)
        if not product:
            errors.append(f"Produto não encontrado: {item.external_id}")
            continue

        changed = False
        if item.name is not None:
            product.name = item.name
            changed = True
        if item.price is not None:
            product.price = item.price
        if item.description is not None:
            product.description = item.description
            changed = True
        if item.image_url is not None:
            product.image_url = item.image_url
        if item.category is not None:
            product.category = item.category
            changed = True
        if item.attributes is not None:
            product.attributes = item.attributes
            changed = True
        if item.is_active is not None:
            product.is_active = item.is_active

        if changed:
            from app.services.ingestion_service import _compute_hash
            new_hash = _compute_hash(
                product.name,
                product.description or "",
                product.attributes or {},
                product.category or [],
            )
            if new_hash != product.data_hash:
                product.data_hash = new_hash
                product.enriched_text = None
                to_enrich.append(product)

        updated += 1

    db.commit()

    if to_enrich:
        background_tasks.add_task(
            _enrich_and_embed,
            products=to_enrich,
            tenant_id=current_user.tenant_id
        )

    return BatchResponse(created=0, updated=updated, unchanged=0, errors=errors)


# ------------------------------------------------------------------ #
# POST /reindex  (força re-enriquecimento Gemini + re-indexação Qdrant)
# GET  /reindex/status  (quantidade de produtos ainda pendentes)
# ------------------------------------------------------------------ #

@router.get("/reindex/status")
def reindex_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total = db.query(Product).filter(Product.tenant_id == current_user.tenant_id, Product.is_active == True).count()
    pending = db.query(Product).filter(Product.tenant_id == current_user.tenant_id, Product.is_active == True, Product.enriched_text == None).count()
    return {"running": pending > 0, "pending": pending, "total": total}

@router.post("/reindex")
def reindex_catalog(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Força o re-enriquecimento de todos os produtos via Gemini e a re-indexação
    completa no Qdrant (com category_prefixes e índices atualizados).
    Retorna imediatamente — o processamento ocorre em background.
    """
    products = db.query(Product).filter(
        Product.tenant_id == current_user.tenant_id,
        Product.is_active == True
    ).all()

    if not products:
        return {"total": 0, "message": "Nenhum produto ativo encontrado."}

    # Zera enriched_text para forçar o Gemini re-processar todos
    for p in products:
        p.enriched_text = None
    db.commit()

    background_tasks.add_task(
        _enrich_and_embed,
        products=products,
        tenant_id=current_user.tenant_id,
        compute_similars=True
    )

    return {"total": len(products), "message": f"{len(products)} produtos enviados para reindexação."}


# ------------------------------------------------------------------ #
# DELETE /batch
# ------------------------------------------------------------------ #

@router.delete("/batch", response_model=BatchResponse)
def delete_products_batch(
    body: ProductDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if len(body.external_ids) > BATCH_LIMIT:
        raise HTTPException(422, f"Máximo de {BATCH_LIMIT} produtos por chamada.")

    deleted = db.query(Product).filter(
        Product.tenant_id == current_user.tenant_id,
        Product.external_id.in_(body.external_ids)
    ).delete(synchronize_session=False)

    db.commit()
    return BatchResponse(created=0, updated=0, unchanged=0, errors=[])
