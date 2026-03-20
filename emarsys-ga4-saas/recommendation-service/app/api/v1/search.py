from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Any
from app.api.deps import get_current_user
from app.db.models import User
from app.services.ai_service import AIService

router = APIRouter()

# Schema de Entrada (O que o usuário envia)
class SearchQuery(BaseModel):
    query: str
    limit: int = 10

# Schema de Saída (O que a API responde)
class SearchResult(BaseModel):
    results: List[Any]

@router.post("/", response_model=SearchResult)
def search_products(
    search_in: SearchQuery,
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint de Busca Semântica.
    Recebe texto livre (ex: "roupa para o frio") e retorna produtos relevantes.
    """
    results = AIService.search(
        query=search_in.query,
        tenant_id=current_user.tenant_id,
        limit=search_in.limit
    )
    
    return {"results": results}