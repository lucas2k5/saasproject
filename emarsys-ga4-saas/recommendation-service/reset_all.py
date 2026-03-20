from qdrant_client import QdrantClient

# Conexão
client = QdrantClient(url="http://localhost:6333")

# Lista todas as coleções
collections = client.get_collections()

print(f"Encontradas {len(collections.collections)} coleções.")

for collection in collections.collections:
    print(f"🗑️ Deletando coleção: {collection.name}")
    client.delete_collection(collection_name=collection.name)

print("✅ Limpeza concluída! O Qdrant está vazio.")
print("Agora faça o upload do CSV novamente para recriar os índices corretamente.")