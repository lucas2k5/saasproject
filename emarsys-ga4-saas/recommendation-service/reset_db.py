import sys
import os

# Adiciona o diretório atual ao path
sys.path.append(os.getcwd())

from sqlalchemy import text
from app.db.session import engine

def fix_database():
    print("🔧 Iniciando correção do banco de dados...")
    
    with engine.connect() as conn:
        # 1. Limpa as tabelas para evitar conflito de dados duplicados ao criar a constraint
        print("🗑️  Limpando tabelas 'products' e 'categories'...")
        try:
            conn.execute(text("TRUNCATE TABLE products CASCADE;"))
            conn.execute(text("TRUNCATE TABLE categories CASCADE;"))
            print("✅ Tabelas limpas.")
        except Exception as e:
            print(f"⚠️  Erro ao limpar (pode ser que tabelas não existam): {e}")

        # 2. Cria a constraint de PRODUTOS
        print("🏗️  Criando constraint uq_product_tenant_extid...")
        try:
            conn.execute(text("""
                ALTER TABLE products 
                ADD CONSTRAINT uq_product_tenant_extid 
                UNIQUE (tenant_id, external_id);
            """))
            print("✅ Constraint de Produtos criada com sucesso!")
        except Exception as e:
            # Se der erro, provavelmente já existe ou a tabela tá errada
            print(f"⚠️  Aviso Produtos: {e}")

        # 3. Cria a constraint de CATEGORIAS
        print("🏗️  Criando constraint uq_category_tenant_path...")
        try:
            conn.execute(text("""
                ALTER TABLE categories 
                ADD CONSTRAINT uq_category_tenant_path 
                UNIQUE (tenant_id, path);
            """))
            print("✅ Constraint de Categorias criada com sucesso!")
        except Exception as e:
            print(f"⚠️  Aviso Categorias: {e}")
            
        conn.commit()
    
    print("\n🚀 Banco de dados corrigido e pronto para uso!")

if __name__ == "__main__":
    fix_database()