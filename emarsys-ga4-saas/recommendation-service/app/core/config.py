# backend/app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "SaaS AI Recommender"
    API_V1_STR: str = "/api/v1"

    # Conexão com o PostgreSQL do Docker
    # Formato: postgresql://usuario:senha@host:porta/banco
    DATABASE_URL: str = "postgresql://admin:admin@localhost:5432/saas_db"

    # Chave para assinar os Tokens (Gerar uma aleatória segura em produção)
    SECRET_KEY: str = "CHAVE_SUPER_SECRETA_DESENVOLVIMENTO_123"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 dias

    GEMINI_API_KEY: str = ""

    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""

    # CORS — origens separadas por vírgula (use "*" para permitir todas em dev)
    CORS_ORIGINS: str = "*"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Read replica para jobs pesados (opcional — fallback: usa DATABASE_URL)
    DATABASE_URL_REPLICA: str = ""

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
