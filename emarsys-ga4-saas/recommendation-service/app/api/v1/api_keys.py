# backend/app/api/v1/api_keys.py
"""
CRUD de API Keys para acesso programático.
Apenas usuários autenticados via JWT podem gerenciar keys.
"""
import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User, ApiKey
from app.api.deps import ALL_SCOPES, oauth2_scheme, _hash_key
from app.core.config import settings
from jose import jwt, JWTError

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_jwt_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Exige JWT — API Keys NÃO podem gerenciar outras API Keys."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(401, "Apenas autenticação JWT é permitida para gerenciar API Keys")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(401, "Token inválido")
    except JWTError:
        raise HTTPException(401, "Token inválido")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(401, "Usuário não encontrado")
    return user


# ---- Schemas ----

class ApiKeyCreate(BaseModel):
    name: str
    scopes: list[str]
    expires_in_days: Optional[int] = None  # null = nunca expira

class ApiKeyUpdate(BaseModel):
    name: Optional[str] = None
    scopes: Optional[list[str]] = None
    is_active: Optional[bool] = None


# ---- Endpoints ----

@router.get("/api-keys")
def list_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(_get_jwt_user),
):
    keys = db.query(ApiKey).filter(
        ApiKey.tenant_id == current_user.tenant_id,
    ).order_by(ApiKey.created_at.desc()).all()
    return [
        {
            "id": str(k.id),
            "name": k.name,
            "key_prefix": k.key_prefix,
            "scopes": k.scopes,
            "is_active": k.is_active,
            "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
            "expires_at": k.expires_at.isoformat() if k.expires_at else None,
            "created_at": k.created_at.isoformat() if k.created_at else None,
        }
        for k in keys
    ]


@router.post("/api-keys")
def create_api_key(
    data: ApiKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_get_jwt_user),
):
    # Valida scopes
    invalid = set(data.scopes) - ALL_SCOPES
    if invalid:
        raise HTTPException(422, f"Scopes inválidos: {', '.join(sorted(invalid))}. Válidos: {', '.join(sorted(ALL_SCOPES))}")
    if not data.scopes:
        raise HTTPException(422, "Pelo menos 1 scope é obrigatório")

    # Gera key segura: sk-<32 chars hex>
    raw_key = f"sk-{secrets.token_hex(32)}"
    key_hash = _hash_key(raw_key)
    key_prefix = raw_key[:12]  # "sk-" + 9 chars

    expires_at = None
    if data.expires_in_days:
        from datetime import timedelta
        expires_at = datetime.now(timezone.utc) + timedelta(days=data.expires_in_days)

    ak = ApiKey(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        name=data.name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        scopes=data.scopes,
        is_active=True,
        expires_at=expires_at,
    )
    db.add(ak)
    db.commit()
    db.refresh(ak)

    logger.info("API Key criada: %s (%s) para tenant %s", ak.name, key_prefix, current_user.tenant_id)

    return {
        "id": str(ak.id),
        "name": ak.name,
        "key_prefix": key_prefix,
        "raw_key": raw_key,  # Mostrada APENAS nesta resposta!
        "scopes": ak.scopes,
        "is_active": True,
        "expires_at": ak.expires_at.isoformat() if ak.expires_at else None,
        "created_at": ak.created_at.isoformat() if ak.created_at else None,
        "message": "Guarde esta key — ela não será exibida novamente!",
    }


@router.put("/api-keys/{key_id}")
def update_api_key(
    key_id: str,
    data: ApiKeyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_get_jwt_user),
):
    ak = db.query(ApiKey).filter(
        ApiKey.id == key_id,
        ApiKey.tenant_id == current_user.tenant_id,
    ).first()
    if not ak:
        raise HTTPException(404, "API Key não encontrada")

    if data.name is not None:
        ak.name = data.name
    if data.scopes is not None:
        invalid = set(data.scopes) - ALL_SCOPES
        if invalid:
            raise HTTPException(422, f"Scopes inválidos: {', '.join(sorted(invalid))}")
        if not data.scopes:
            raise HTTPException(422, "Pelo menos 1 scope é obrigatório")
        ak.scopes = data.scopes
    if data.is_active is not None:
        ak.is_active = data.is_active

    db.commit()
    db.refresh(ak)
    return {
        "id": str(ak.id),
        "name": ak.name,
        "key_prefix": ak.key_prefix,
        "scopes": ak.scopes,
        "is_active": ak.is_active,
        "last_used_at": ak.last_used_at.isoformat() if ak.last_used_at else None,
        "expires_at": ak.expires_at.isoformat() if ak.expires_at else None,
        "created_at": ak.created_at.isoformat() if ak.created_at else None,
    }


@router.delete("/api-keys/{key_id}")
def revoke_api_key(
    key_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(_get_jwt_user),
):
    ak = db.query(ApiKey).filter(
        ApiKey.id == key_id,
        ApiKey.tenant_id == current_user.tenant_id,
    ).first()
    if not ak:
        raise HTTPException(404, "API Key não encontrada")

    ak.is_active = False
    db.commit()
    return {"revoked": True, "key_prefix": ak.key_prefix}


@router.get("/api-keys/scopes")
def list_available_scopes(
    current_user: User = Depends(_get_jwt_user),
):
    """Retorna todos os scopes disponíveis com descrição."""
    scope_descriptions = {
        "catalog:read": "Consultar produtos, preços, estoque, ofertas, lojas e canais",
        "catalog:write": "Importar/atualizar produtos, preços, estoque, ofertas, lojas e canais",
        "customers:read": "Consultar clientes e segmentos de lifecycle",
        "customers:write": "Importar/atualizar clientes e pedidos",
        "recommendations:read": "Consultar recomendações (individual e batch)",
        "recommendations:run": "Disparar jobs de recomendação e lifecycle",
        "content:read": "Consultar conteúdo gerado (email, whatsapp, push)",
        "content:run": "Disparar jobs de geração de conteúdo",
        "content:templates": "Gerenciar templates de conteúdo",
        "search": "Busca semântica no catálogo",
        "config": "Gerenciar configurações do tenant",
        "dashboard": "Acessar métricas e estatísticas",
        "lifecycle:read": "Consultar segmentos de ciclo de vida",
        "lifecycle:run": "Disparar jobs de segmentação",
        "admin": "Operações administrativas (purge, etc.)",
    }
    return [{"scope": s, "description": scope_descriptions.get(s, "")} for s in sorted(ALL_SCOPES)]
