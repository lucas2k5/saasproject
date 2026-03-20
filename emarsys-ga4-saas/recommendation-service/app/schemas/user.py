# backend/app/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional

# O que o utilizador envia para se registar
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company_name: str

# O que a API responde (Token)
class Token(BaseModel):
    access_token: str
    token_type: str

# Dados dentro do Token
class TokenPayload(BaseModel):
    sub: Optional[str] = None
    tenant_id: Optional[str] = None