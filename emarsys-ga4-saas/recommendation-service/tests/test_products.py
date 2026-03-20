"""
Testes do endpoint POST /api/v1/products/batch.

Premissa: o banco já tem produtos carregados via CSV.
Os testes inserem dados próprios com prefixo TEST_ e limpam ao final.
"""
import pytest
import httpx

PREFIX = "TEST_PROD_"

SAMPLE_PRODUCTS = [
    {
        "external_id": f"{PREFIX}001",
        "name": "Tênis Running Pro",
        "price": 299.90,
        "description": "Tênis para corrida com amortecimento avançado",
        "image_url": "https://example.com/tenis.jpg",
        "category": ["Calçados > Esportivos"],
        "attributes": {"cor": "preto", "tamanho": "42", "material": "mesh"},
        "is_active": True,
    },
    {
        "external_id": f"{PREFIX}002",
        "name": "Camiseta Dry Fit",
        "price": 89.90,
        "description": "Camiseta para treino com tecnologia dry fit",
        "image_url": "https://example.com/camiseta.jpg",
        "category": ["Roupas > Esportivas > Masculino"],
        "attributes": {"cor": "azul", "tamanho": "M"},
        "is_active": True,
    },
    {
        "external_id": f"{PREFIX}003",
        "name": "Mochila Urbana 30L",
        "price": 199.00,
        "description": "Mochila resistente com compartimento para notebook",
        "category": ["Acessórios > Bolsas"],
        "attributes": {"capacidade": "30L", "cor": "cinza"},
        "is_active": True,
    },
]


class TestProductBatch:

    def test_upsert_creates_new_products(self, client: httpx.Client):
        resp = client.post("/api/v1/products/batch", json={"items": SAMPLE_PRODUCTS})
        assert resp.status_code == 200
        data = resp.json()
        assert data["created"] == 3
        assert data["updated"] == 0
        assert data["unchanged"] == 0

    def test_upsert_same_data_marks_unchanged(self, client: httpx.Client):
        """Segunda chamada com dados idênticos — hash igual, deve ser unchanged."""
        resp = client.post("/api/v1/products/batch", json={"items": SAMPLE_PRODUCTS})
        assert resp.status_code == 200
        data = resp.json()
        assert data["unchanged"] == 3
        assert data["created"] == 0
        assert data["updated"] == 0

    def test_upsert_changed_data_triggers_update(self, client: httpx.Client):
        """Altera o nome de um produto — deve contar como updated."""
        modified = [dict(SAMPLE_PRODUCTS[0], name="Tênis Running Pro EDITADO")]
        resp = client.post("/api/v1/products/batch", json={"items": modified})
        assert resp.status_code == 200
        data = resp.json()
        assert data["updated"] == 1

    def test_upsert_limit_exceeded(self, client: httpx.Client):
        """Mais de 1000 itens deve retornar 422."""
        big_batch = [
            {"external_id": f"{PREFIX}LIMIT_{i}", "name": f"Prod {i}", "price": 10.0}
            for i in range(1001)
        ]
        resp = client.post("/api/v1/products/batch", json={"items": big_batch})
        assert resp.status_code == 422

    def test_list_products(self, client: httpx.Client):
        resp = client.get("/api/v1/products/", params={"q": "TEST_PROD"})
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) >= 3

    def test_get_product_by_external_id(self, client: httpx.Client):
        resp = client.get(f"/api/v1/products/{PREFIX}001")
        assert resp.status_code == 200
        assert resp.json()["external_id"] == f"{PREFIX}001"

    def test_patch_batch(self, client: httpx.Client):
        resp = client.patch("/api/v1/products/batch", json={"items": [
            {"external_id": f"{PREFIX}002", "price": 79.90, "is_active": False}
        ]})
        assert resp.status_code == 200
        assert resp.json()["updated"] == 1

    def test_patch_nonexistent_returns_error(self, client: httpx.Client):
        resp = client.patch("/api/v1/products/batch", json={"items": [
            {"external_id": "NAO_EXISTE_XYZ", "price": 10.0}
        ]})
        assert resp.status_code == 200
        assert len(resp.json()["errors"]) == 1

    def test_delete_batch(self, client: httpx.Client):
        resp = client.request(
            "DELETE",
            "/api/v1/products/batch",
            json={"external_ids": [f"{PREFIX}001", f"{PREFIX}002", f"{PREFIX}003"]},
        )
        assert resp.status_code == 200

    def test_deleted_product_not_found(self, client: httpx.Client):
        resp = client.get(f"/api/v1/products/{PREFIX}001")
        assert resp.status_code == 404
