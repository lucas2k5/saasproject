from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_current_user
from app.db.session import get_db
from app.db.models import User, Product, TenantConfig
from app.services.ai_service import AIService

router = APIRouter()

def is_valid_uuid(val: str):
    """Verifica se a string é um UUID válido."""
    try:
        UUID(val)
        return True
    except ValueError:
        return False

@router.get("/{product_identifier}")
def get_product_recommendations(
    product_identifier: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retorna recomendações para a Página de Produto (PDP).
    
    Aceita:
    - UUID (ID Interno): ex "550e8400-e29b..."
    - SKU (ID Externo): ex "SKU-2007"
    """
    target_uuid = product_identifier

    # 1. Se NÃO for um UUID, assumimos que é um SKU e buscamos no SQL
    if not is_valid_uuid(product_identifier):
        product = db.query(Product).filter(
            Product.tenant_id == current_user.tenant_id,
            Product.external_id == product_identifier
        ).first()
        
        if not product:
            raise HTTPException(
                status_code=404, 
                detail=f"Produto com SKU '{product_identifier}' não encontrado."
            )
        
        # Traduzimos para o ID que o Qdrant entende
        target_uuid = str(product.id)

    config = db.query(TenantConfig).filter(TenantConfig.tenant_id == current_user.tenant_id).first()
    recommendation_limit = config.recommendation_limit if config else 10
    similarity = config.similarity_threshold if config else 0.7
    low = config.price_threshold_low if config else 0.9
    high = config.price_threshold_high if config else 1.1
    category_level = config.recommendation_category_level if config else 0

    # 2. Chama a IA usando o UUID (seja ele passado direto ou descoberto acima)
    result = AIService.recommend(
        product_id=target_uuid,
        tenant_id=current_user.tenant_id,
        limit=recommendation_limit,
        price_low=low,
        price_high=high,
        similarity=similarity,
        category_level=category_level
    )
    
    if result is None:
        raise HTTPException(
            status_code=404, 
            detail="Produto encontrado no SQL, mas ainda não indexado na IA. Tente reprocessar o arquivo."
        )
    
    return result