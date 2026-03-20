"""
Fixtures compartilhadas entre todos os testes.

Os testes rodam contra o servidor local em http://localhost:8000.
Certifique-se de que o servidor está no ar antes de executar.

Variáveis de ambiente necessárias (ou ajuste as constantes abaixo):
  TEST_EMAIL    e-mail de um usuário já cadastrado no ambiente
  TEST_PASSWORD senha desse usuário
  BASE_URL      base URL da API (default: http://localhost:8000)
"""
import os
import pytest
import httpx

BASE_URL   = os.getenv("BASE_URL",    "http://localhost:8000")
TEST_EMAIL = os.getenv("TEST_EMAIL",  "admin@teste.com")
TEST_PWD   = os.getenv("TEST_PASSWORD", "senha123")


@pytest.fixture(scope="session")
def token() -> str:
    """Faz login uma vez por sessão de testes e retorna o Bearer token."""
    resp = httpx.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={"username": TEST_EMAIL, "password": TEST_PWD},
    )
    assert resp.status_code == 200, f"Login falhou: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def headers(token) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def client(headers) -> httpx.Client:
    """Cliente HTTP reutilizável com autenticação já configurada."""
    return httpx.Client(base_url=BASE_URL, headers=headers, timeout=30)
