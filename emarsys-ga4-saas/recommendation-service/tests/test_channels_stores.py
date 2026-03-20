"""
Testes de canais e lojas.
Canal com stores embutidas cria/vincula lojas automaticamente.
"""
import pytest
import httpx

PREFIX = "TEST_"

SAMPLE_CHANNELS = [
    {
        "channel_id": f"{PREFIX}CH_WEB",
        "name": "E-commerce",
        "type": "web",
        "store_mode": "single",
        "stores": [],
    },
    {
        "channel_id": f"{PREFIX}CH_APP",
        "name": "App Mobile",
        "type": "app",
        "store_mode": "multi",
        "stores": [
            {"store_id": f"{PREFIX}LOJA_01", "name": "Loja Centro"},
            {"store_id": f"{PREFIX}LOJA_02", "name": "Loja Norte"},
        ],
    },
    {
        "channel_id": f"{PREFIX}CH_FISICO",
        "name": "Lojas Físicas",
        "type": "loja_fisica",
        "store_mode": "multi",
        "stores": [
            {"store_id": f"{PREFIX}LOJA_01", "name": "Loja Centro"},   # mesma loja, 2 canais
            {"store_id": f"{PREFIX}LOJA_03", "name": "Loja Sul"},
        ],
    },
]


class TestChannelBatch:

    def test_upsert_creates_channels_and_stores(self, client: httpx.Client):
        resp = client.post("/api/v1/channels/batch", json=SAMPLE_CHANNELS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["created"] == 3

    def test_stores_were_created(self, client: httpx.Client):
        """As lojas embutidas nos canais devem ter sido criadas na tabela stores."""
        resp = client.get("/api/v1/stores/")
        assert resp.status_code == 200
        store_ids = [s["store_id"] for s in resp.json()]
        assert f"{PREFIX}LOJA_01" in store_ids
        assert f"{PREFIX}LOJA_02" in store_ids
        assert f"{PREFIX}LOJA_03" in store_ids

    def test_upsert_same_channels_updates(self, client: httpx.Client):
        resp = client.post("/api/v1/channels/batch", json=SAMPLE_CHANNELS)
        assert resp.status_code == 200
        assert resp.json()["updated"] == 3

    def test_list_channels(self, client: httpx.Client):
        resp = client.get("/api/v1/channels/")
        assert resp.status_code == 200
        channel_ids = [c["channel_id"] for c in resp.json()]
        assert f"{PREFIX}CH_WEB" in channel_ids

    def test_get_channel(self, client: httpx.Client):
        resp = client.get(f"/api/v1/channels/{PREFIX}CH_APP")
        assert resp.status_code == 200
        data = resp.json()
        assert data["store_mode"] == "multi"
        assert data["type"] == "app"

    def test_patch_channel(self, client: httpx.Client):
        resp = client.patch("/api/v1/channels/batch", json=[
            {"channel_id": f"{PREFIX}CH_WEB", "name": "E-commerce Principal", "is_active": True}
        ])
        assert resp.status_code == 200
        assert resp.json()["updated"] == 1

        resp2 = client.get(f"/api/v1/channels/{PREFIX}CH_WEB")
        assert resp2.json()["name"] == "E-commerce Principal"

    def test_patch_channel_stores_replaces_links(self, client: httpx.Client):
        """Patch com stores deve substituir os vínculos existentes."""
        resp = client.patch("/api/v1/channels/batch", json=[
            {
                "channel_id": f"{PREFIX}CH_APP",
                "stores": [
                    {"store_id": f"{PREFIX}LOJA_01", "name": "Loja Centro"},
                    {"store_id": f"{PREFIX}LOJA_04", "name": "Loja Leste"},
                ],
            }
        ])
        assert resp.status_code == 200

    def test_limit_exceeded(self, client: httpx.Client):
        big = [
            {"channel_id": f"{PREFIX}LIMIT_{i}", "name": f"Canal {i}", "type": "web", "store_mode": "single"}
            for i in range(1001)
        ]
        resp = client.post("/api/v1/channels/batch", json=big)
        assert resp.status_code == 422

    def test_delete_channels(self, client: httpx.Client):
        resp = client.request(
            "DELETE",
            "/api/v1/channels/batch",
            json={"channel_ids": [f"{PREFIX}CH_WEB", f"{PREFIX}CH_APP", f"{PREFIX}CH_FISICO"]},
        )
        assert resp.status_code == 200

    def test_delete_stores(self, client: httpx.Client):
        resp = client.request(
            "DELETE",
            "/api/v1/stores/batch",
            json={"store_ids": [
                f"{PREFIX}LOJA_01", f"{PREFIX}LOJA_02",
                f"{PREFIX}LOJA_03", f"{PREFIX}LOJA_04",
            ]},
        )
        assert resp.status_code == 200


class TestStoreBatch:

    def test_upsert_stores(self, client: httpx.Client):
        resp = client.post("/api/v1/stores/batch", json=[
            {"store_id": f"{PREFIX}ST_001", "name": "Loja Teste A", "is_active": True},
            {"store_id": f"{PREFIX}ST_002", "name": "Loja Teste B", "is_active": True},
        ])
        assert resp.status_code == 200
        assert resp.json()["created"] == 2

    def test_patch_store(self, client: httpx.Client):
        resp = client.patch("/api/v1/stores/batch", json=[
            {"store_id": f"{PREFIX}ST_001", "name": "Loja Teste A — Editada"}
        ])
        assert resp.status_code == 200
        assert resp.json()["updated"] == 1

    def test_delete_stores_cleanup(self, client: httpx.Client):
        resp = client.request(
            "DELETE",
            "/api/v1/stores/batch",
            json={"store_ids": [f"{PREFIX}ST_001", f"{PREFIX}ST_002"]},
        )
        assert resp.status_code == 200
