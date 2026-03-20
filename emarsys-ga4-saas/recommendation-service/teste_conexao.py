import asyncio
import asyncpg
from qdrant_client import QdrantClient

# Configurações do Docker (que definimos no docker-compose.yml)
DB_CONFIG = "postgresql://admin:admin@localhost:5432/saas_db"
QDRANT_URL = "http://localhost:6333"

async def testar_postgres():
    try:
        print("⏳ Tentando conectar ao PostgreSQL...")
        conn = await asyncpg.connect(DB_CONFIG)
        version = await conn.fetchval("SELECT version()")
        print(f"✅ SUCESSO! Conectado ao: {version}")
        await conn.close()
    except Exception as e:
        print(f"❌ ERRO no PostgreSQL: {e}")

def testar_qdrant():
    try:
        print("\n⏳ Tentando conectar ao Qdrant (IA)...")
        client = QdrantClient(url=QDRANT_URL)
        collections = client.get_collections()
        print(f"✅ SUCESSO! Qdrant respondendo. Coleções ativas: {len(collections.collections)}")
    except Exception as e:
        print(f"❌ ERRO no Qdrant: {e}")

async def main():
    await testar_postgres()
    testar_qdrant()

if __name__ == "__main__":
    asyncio.run(main())