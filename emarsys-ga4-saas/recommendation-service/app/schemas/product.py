from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from uuid import UUID  # <--- 1. Importante: Adicione este import

# --- 1. SCHEMAS DE RESPOSTA AUXILIARES ---
class IngestionSummary(BaseModel):
    total_processed: int
    tenant_id: str
    status: str
    message: str

# --- 2. SCHEMAS DE ENTRADA (WRITE) ---
class ProductCreate(BaseModel):
    external_id: str
    name: str
    price: float
    description: Optional[str] = None
    image_url: Optional[str] = None
    category: List[str] = []
    attributes: Dict[str, Any] = {}

# --- 3. SCHEMAS DE SAÍDA (READ) ---

# Base comum de leitura
class ProductReadBase(BaseModel):
    id: UUID  # <--- 2. Correção: Mudamos de 'int' para 'UUID'
    external_id: str
    name: str
    price: float
    description: Optional[str] = None
    image_url: Optional[str] = None
    category: Any
    tenant_id: str

    class Config:
        from_attributes = True

# VISÃO 1: LEVE (Para o Grid/Lista)
class ProductResponse(ProductReadBase):
    pass

# VISÃO 2: PESADA (Para a PDP/Gaveta)
class ProductDetailResponse(ProductReadBase):
    attributes: Dict[str, Any] = {}
    enriched_text: Optional[str] = None
    purchase_cycle_type: Optional[str] = None
    purchase_cycle_days: Optional[int] = None
