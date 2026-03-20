"""
Testes de preços e estoque por canal/loja.

Depende de:
  - Produto com external_id TEST_PS_PROD existindo (criado no setUp)
  - Canal com channel_id TEST_PS_CH existindo (criado no setUp)
  - Loja com store_id TEST_PS_LOJA existindo (criado no setUp)

Todos criados como fixture de sessão e removidos no teardown.
"""
import pytest
import httpx

PREFIX = "TEST_PS_"

PROD = {"external_id": f"{PREFIX}PROD", "name": "Produto Preço/Estoque", "price": 100.0}
CHAN = {"channel_id": f"{PREFIX}CH", "name": "Canal Teste PS", "type": "web", "store_mode": "multi",
        "stores": [
            {"store_id": f"{PREFIX}LOJA", "name": "Loja Teste PS"},
            {"store_id": f"{PREFIX}LOJA2", "name": "Loja Teste PS 2"},
        ]}


@pytest.fixture(scope="class", autouse=True)
def setup_dependencies(client: httpx.Client):
    """Cria produto, canal e loja necessários para os testes de preço/estoque."""
    client.post("/api/v1/products/batch", json={"items": [PROD]})
    client.post("/api/v1/channels/batch", json=[CHAN])
    yield
    # Teardown
    client.request("DELETE", "/api/v1/products/batch",
                   json={"external_ids": [f"{PREFIX}PROD"]})
    client.request("DELETE", "/api/v1/channels/batch",
                   json={"channel_ids": [f"{PREFIX}CH"]})
    client.request("DELETE", "/api/v1/stores/batch",
                   json={"store_ids": [f"{PREFIX}LOJA", f"{PREFIX}LOJA2"]})


class TestPriceBatch:

    def test_upsert_price_by_store(self, client: httpx.Client):
        """Preço para uma loja específica."""
        resp = client.post("/api/v1/prices/batch", json=[
            {"product_external_id": f"{PREFIX}PROD", "channel_id": f"{PREFIX}CH",
             "store_id": f"{PREFIX}LOJA", "price": 89.90}
        ])
        assert resp.status_code == 200
        assert resp.json()["created"] == 1

    def test_upsert_price_second_store(self, client: httpx.Client):
        """Preço para segunda loja."""
        resp = client.post("/api/v1/prices/batch", json=[
            {"product_external_id": f"{PREFIX}PROD", "channel_id": f"{PREFIX}CH",
             "store_id": f"{PREFIX}LOJA2", "price": 84.90}
        ])
        assert resp.status_code == 200
        assert resp.json()["created"] == 1

    def test_upsert_updates_existing_price(self, client: httpx.Client):
        """Segunda chamada com preço diferente deve sobrescrever."""
        resp = client.post("/api/v1/prices/batch", json=[
            {"product_external_id": f"{PREFIX}PROD", "channel_id": f"{PREFIX}CH",
             "store_id": f"{PREFIX}LOJA", "price": 79.90}
        ])
        assert resp.status_code == 200

    def test_error_nonexistent_product(self, client: httpx.Client):
        resp = client.post("/api/v1/prices/batch", json=[
            {"product_external_id": "NAO_EXISTE_XYZ", "channel_id": f"{PREFIX}CH", "price": 50.0}
        ])
        assert resp.status_code == 200
        assert len(resp.json()["errors"]) == 1

    def test_error_nonexistent_channel(self, client: httpx.Client):
        resp = client.post("/api/v1/prices/batch", json=[
            {"product_external_id": f"{PREFIX}PROD", "channel_id": "CANAL_INEXISTENTE", "price": 50.0}
        ])
        assert resp.status_code == 200
        assert len(resp.json()["errors"]) == 1

    def test_list_prices_by_product(self, client: httpx.Client):
        resp = client.get("/api/v1/prices/",
                          params={"product_external_id": f"{PREFIX}PROD"})
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_delete_price(self, client: httpx.Client):
        resp = client.request("DELETE", "/api/v1/prices/batch", json={"items": [
            {"product_external_id": f"{PREFIX}PROD", "channel_id": f"{PREFIX}CH", "store_id": f"{PREFIX}LOJA"}
        ]})
        assert resp.status_code == 200


class TestStockBatch:

    def test_upsert_stock_by_store(self, client: httpx.Client):
        resp = client.post("/api/v1/stock/batch", json=[
            {"product_external_id": f"{PREFIX}PROD", "channel_id": f"{PREFIX}CH",
             "store_id": f"{PREFIX}LOJA", "quantity": 50, "available": True}
        ])
        assert resp.status_code == 200
        assert resp.json()["created"] == 1

    def test_upsert_stock_second_store(self, client: httpx.Client):
        resp = client.post("/api/v1/stock/batch", json=[
            {"product_external_id": f"{PREFIX}PROD", "channel_id": f"{PREFIX}CH",
             "store_id": f"{PREFIX}LOJA2", "quantity": 12, "available": True}
        ])
        assert resp.status_code == 200
        assert resp.json()["created"] == 1

    def test_patch_stock(self, client: httpx.Client):
        resp = client.patch("/api/v1/stock/batch", json=[
            {"product_external_id": f"{PREFIX}PROD", "channel_id": f"{PREFIX}CH",
             "store_id": f"{PREFIX}LOJA", "quantity": 0, "available": False}
        ])
        assert resp.status_code == 200
        assert resp.json()["updated"] == 1

    def test_list_stock_available_only(self, client: httpx.Client):
        resp = client.get("/api/v1/stock/", params={"available_only": True})
        assert resp.status_code == 200
        items = resp.json()
        assert all(i["available"] for i in items)

    def test_list_stock_by_product(self, client: httpx.Client):
        resp = client.get("/api/v1/stock/",
                          params={"product_external_id": f"{PREFIX}PROD"})
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_delete_stock(self, client: httpx.Client):
        resp = client.request("DELETE", "/api/v1/stock/batch", json={"items": [
            {"product_external_id": f"{PREFIX}PROD", "channel_id": f"{PREFIX}CH",
             "store_id": f"{PREFIX}LOJA"},
            {"product_external_id": f"{PREFIX}PROD", "channel_id": f"{PREFIX}CH",
             "store_id": f"{PREFIX}LOJA2"},
        ]})
        assert resp.status_code == 200
