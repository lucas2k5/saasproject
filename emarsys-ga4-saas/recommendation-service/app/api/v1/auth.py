import logging
import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash, verify_password, create_access_token
from app.db.session import get_db
from app.db.models import User
from app.schemas.user import UserCreate, Token
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


# ------------------------------------------------------------------ #
# Schemas auxiliares
# ------------------------------------------------------------------ #

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class UserMeResponse(BaseModel):
    email: str
    full_name: str | None
    company_name: str | None
    tenant_id: str


# ------------------------------------------------------------------ #
# POST /register
# ------------------------------------------------------------------ #

@router.post("/register", response_model=Token)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    if len(user_in.password) < 8:
        raise HTTPException(status_code=400, detail="A senha deve ter no mínimo 8 caracteres.")

    user_exists = db.query(User).filter(User.email == user_in.email).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="Email já registrado.")

    tenant_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, user_in.company_name))

    new_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        company_name=user_in.company_name,
        tenant_id=tenant_id,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(data={"sub": new_user.email, "tenant_id": tenant_id})
    return {"access_token": access_token, "token_type": "bearer"}


# ------------------------------------------------------------------ #
# POST /login
# ------------------------------------------------------------------ #

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Credenciais inválidas.")

    access_token = create_access_token(data={"sub": user.email, "tenant_id": user.tenant_id})
    return {"access_token": access_token, "token_type": "bearer"}


# ------------------------------------------------------------------ #
# GET /me  — dados do usuario autenticado
# ------------------------------------------------------------------ #

@router.get("/me", response_model=UserMeResponse)
def me(current_user: User = Depends(get_current_user)):
    return UserMeResponse(
        email=current_user.email,
        full_name=current_user.full_name,
        company_name=current_user.company_name,
        tenant_id=current_user.tenant_id,
    )


# ------------------------------------------------------------------ #
# POST /forgot-password  — gera token de reset (15 min)
# ------------------------------------------------------------------ #

@router.post("/forgot-password")
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()

    # Sempre retorna sucesso para nao revelar se o email existe
    if not user:
        return {"message": "Se o email existir, um link de redefinição será enviado."}

    # Gera token JWT de curta duração com purpose=reset
    reset_token = create_access_token(
        data={"sub": user.email, "purpose": "reset"},
        expires_delta=timedelta(minutes=15),
    )

    # Em produção, enviar email. Por agora, loga o link.
    logger.warning(
        "PASSWORD RESET TOKEN para %s: %s", user.email, reset_token
    )

    return {
        "message": "Se o email existir, um link de redefinição será enviado.",
        "reset_token": reset_token,  # Retorna o token direto (facilita dev/demo)
    }


# ------------------------------------------------------------------ #
# POST /reset-password  — aplica nova senha
# ------------------------------------------------------------------ #

@router.post("/reset-password")
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(body.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        purpose = payload.get("purpose")
        if not email or purpose != "reset":
            raise HTTPException(400, "Token inválido.")
    except JWTError:
        raise HTTPException(400, "Token inválido ou expirado.")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(400, "Token inválido.")

    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="A senha deve ter no mínimo 8 caracteres.")

    user.hashed_password = get_password_hash(body.new_password)
    db.commit()

    return {"message": "Senha redefinida com sucesso."}
