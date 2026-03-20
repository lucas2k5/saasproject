"""
Testes do CRUD batch de /api/v1/customers.
"""
import pytest
import httpx

PREFIX = "TEST_CLI_"

SAMPLE_CUSTOMERS = [
    {
        "customer_id": f"{PREFIX}001",
        "name": "Restaurante do João",
        "customer_add_id": "CRM-001",
        "document": "12.345.678/0001-90",
        "customer_type": "restaurante",
        "source_created_at": "2023-06-01T00:00:00Z",
    },
    {
        "customer_id": f"{PREFIX}002",
        "name": "Padaria Central",
        "document": "98.765.432/0001-10",
        "customer_type": "padaria",
    },
    {
        "customer_id": f"{PREFIX}003",
        "name": "Mercado Bom Preço",
        "customer_type": "supermercado",
    },
]


class TestCustomerBatch:

    def test_upsert_creates(self, client: httpx.Client):
        resp = client.post("/api/v1/customers/batch", json=SAMPLE_CUSTOMERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["created"] == 3
        assert data["updated"] == 0

    def test_upsert_same_data_updates(self, client: httpx.Client):
        """Clientes não têm hash — toda re-chamada conta como updated."""
        resp = client.post("/api/v1/customers/batch", json=SAMPLE_CUSTOMERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["updated"] == 3

    def test_upsert_limit_exceeded(self, client: httpx.Client):
        big_batch = [
            {"customer_id": f"{PREFIX}LIMIT_{i}", "name": f"Cliente {i}"}
            for i in range(1001)
        ]
        resp = client.post("/api/v1/customers/batch", json=big_batch)
        assert resp.status_code == 422

    def test_list_customers(self, client: httpx.Client):
        resp = client.get("/api/v1/customers/", params={"q": "TEST_CLI"})
        assert resp.status_code == 200
        assert len(resp.json()) >= 3

    def test_list_filter_by_type(self, client: httpx.Client):
        resp = client.get("/api/v1/customers/", params={"customer_type": "padaria"})
        assert resp.status_code == 200
        items = resp.json()
        assert all(c["customer_type"] == "padaria" for c in items)

    def test_get_by_customer_id(self, client: httpx.Client):
        resp = client.get(f"/api/v1/customers/{PREFIX}001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["customer_id"] == f"{PREFIX}001"
        assert data["customer_add_id"] == "CRM-001"

    def test_get_not_found(self, client: httpx.Client):
        resp = client.get("/api/v1/customers/NAO_EXISTE_XYZ")
        assert resp.status_code == 404

    def test_patch_batch(self, client: httpx.Client):
        resp = client.patch("/api/v1/customers/batch", json=[
            {
                "customer_id": f"{PREFIX}002",
                "customer_type": "padaria_artesanal",
                "customer_add_id": "CRM-999",
            }
        ])
        assert resp.status_code == 200
        assert resp.json()["updated"] == 1

        # Confirma alteração
        resp2 = client.get(f"/api/v1/customers/{PREFIX}002")
        assert resp2.json()["customer_type"] == "padaria_artesanal"
        assert resp2.json()["customer_add_id"] == "CRM-999"

    def test_patch_nonexistent_returns_error(self, client: httpx.Client):
        resp = client.patch("/api/v1/customers/batch", json=[
            {"customer_id": "NAO_EXISTE_XYZ", "name": "X"}
        ])
        assert resp.status_code == 200
        assert len(resp.json()["errors"]) == 1

    def test_delete_batch(self, client: httpx.Client):
        resp = client.request(
            "DELETE",
            "/api/v1/customers/batch",
            json={"customer_ids": [f"{PREFIX}001", f"{PREFIX}002", f"{PREFIX}003"]},
        )
        assert resp.status_code == 200

    def test_deleted_not_found(self, client: httpx.Client):
        resp = client.get(f"/api/v1/customers/{PREFIX}001")
        assert resp.status_code == 404
