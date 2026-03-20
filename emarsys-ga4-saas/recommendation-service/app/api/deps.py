from typing import Optional
import hashlib
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.db.models import User, Customer, ApiKey

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)

VALID_ID_TYPES = {"customer_id", "customer_add_id", "internal"}

ALL_SCOPES = {
    "catalog:read", "catalog:write",
    "customers:read", "customers:write",
    "recommendations:read", "recommendations:run",
    "content:read", "content:run", "content:templates",
    "search",
    "config",
    "dashboard",
    "lifecycle:read", "lifecycle:run",
    "admin",
}


class AuthResult:
    """Resultado de autenticação — funciona tanto para JWT quanto API Key."""
    def __init__(self, tenant_id: str, user: Optional[User] = None, api_key: Optional[ApiKey] = None):
        self.tenant_id = tenant_id
        self.user = user
        self.api_key = api_key
        self._scopes = set(api_key.scopes) if api_key else ALL_SCOPES  # JWT = acesso total

    def require_scope(self, scope: str):
        if scope not in self._scopes:
            raise HTTPException(403, f"API Key não possui o scope '{scope}'")


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
) -> User:
    """Autentica via JWT Bearer token. Mantém compatibilidade com todos os endpoints existentes."""
    # 1. Tenta JWT
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            email: str = payload.get("sub")
            if email:
                user = db.query(User).filter(User.email == email).first()
                if user:
                    return user
        except JWTError:
            pass

    # 2. Tenta API Key
    api_key_header = request.headers.get("X-API-Key")
    if api_key_header:
        key_hash = _hash_key(api_key_header)
        ak = db.query(ApiKey).filter(
            ApiKey.key_hash == key_hash,
            ApiKey.is_active == True,
        ).first()
        if ak:
            if ak.expires_at and ak.expires_at < datetime.now(timezone.utc):
                raise HTTPException(401, "API Key expirada")
            # Atualiza last_used_at (fire-and-forget, não falha se der erro)
            try:
                ak.last_used_at = datetime.now(timezone.utc)
                db.commit()
            except Exception:
                db.rollback()
            # Retorna um User-like object para manter compatibilidade
            # Cria um User virtual com tenant_id da key
            virtual_user = User()
            virtual_user.id = ak.id
            virtual_user.tenant_id = ak.tenant_id
            virtual_user.email = f"apikey:{ak.name}"
            virtual_user.full_name = ak.name
            virtual_user.company_name = None
            virtual_user.is_active = True
            # Attach api_key e scopes para checagem posterior
            virtual_user._api_key = ak
            virtual_user._scopes = set(ak.scopes)
            return virtual_user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_scope(scope: str):
    """Dependency factory para exigir um scope específico da API Key."""
    def _check(current_user: User = Depends(get_current_user)):
        scopes = getattr(current_user, '_scopes', None)
        if scopes is not None and scope not in scopes:
            raise HTTPException(403, f"API Key não possui o scope '{scope}'")
        return current_user
    return _check


def resolve_customer(db: Session, tenant_id: str, ref: str, id_type: str = "customer_id") -> Customer:
    """
    Busca cliente por qualquer tipo de ID.
    id_type: 'customer_id' (ERP), 'customer_add_id' (CRM) ou 'internal' (UUID).
    """
    if id_type not in VALID_ID_TYPES:
        raise HTTPException(422, f"id_type inválido: {id_type}. Use: {', '.join(sorted(VALID_ID_TYPES))}")
    q = db.query(Customer).filter(Customer.tenant_id == tenant_id)
    if id_type == "customer_id":
        q = q.filter(Customer.customer_id == ref)
    elif id_type == "customer_add_id":
        q = q.filter(Customer.customer_add_id == ref)
    else:  # internal
        q = q.filter(Customer.id == ref)
    c = q.first()
    if not c:
        raise HTTPException(404, "Cliente não encontrado")
    return c


def resolve_customers(db: Session, tenant_id: str, ids: list[str], id_type: str = "customer_id") -> list[Customer]:
    """
    Busca múltiplos clientes por lista de IDs.
    Retorna apenas os encontrados (sem erro para IDs inexistentes).
    """
    if id_type not in VALID_ID_TYPES:
        raise HTTPException(422, f"id_type inválido: {id_type}. Use: {', '.join(sorted(VALID_ID_TYPES))}")
    if not ids:
        return []
    q = db.query(Customer).filter(Customer.tenant_id == tenant_id)
    if id_type == "customer_id":
        q = q.filter(Customer.customer_id.in_(ids))
    elif id_type == "customer_add_id":
        q = q.filter(Customer.customer_add_id.in_(ids))
    else:  # internal
        q = q.filter(Customer.id.in_(ids))
    return q.all()
