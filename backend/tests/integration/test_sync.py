"""Esqueleto de sincronización: contrato de /sync/push y /sync/pull."""

from httpx import ASGITransport, AsyncClient

from app.main import app


async def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _token(client: AsyncClient) -> str:
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "company_name": "Sync Co",
            "company_slug": "sync-co",
            "email": "owner@sync.co",
            "password": "password123",
        },
    )
    return r.json()["access_token"]


async def test_push_requiere_autenticacion() -> None:
    async with await _client() as client:
        r = await client.post("/api/v1/sync/push", json={"changes": []})
    assert r.status_code in (401, 403)


async def test_push_entidad_no_soportada() -> None:
    async with await _client() as client:
        token = await _token(client)
        r = await client.post(
            "/api/v1/sync/push",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "changes": [
                    {
                        "entity": "cosa_desconocida",
                        "id": "019f6868-9a2c-75b7-8cf1-36e2316aed71",
                        "op": "upsert",
                        "version": 1,
                        "updated_at": "2026-07-15T12:00:00Z",
                        "data": {},
                    }
                ]
            },
        )
    assert r.status_code == 200
    assert r.json()["results"][0]["status"] == "unsupported"


async def test_pull_devuelve_cursor() -> None:
    async with await _client() as client:
        token = await _token(client)
        r = await client.get(
            "/api/v1/sync/pull", headers={"Authorization": f"Bearer {token}"}
        )
    assert r.status_code == 200
    body = r.json()
    assert body["changes"] == []
    assert isinstance(body["cursor"], str)


async def test_garment_push_y_pull() -> None:
    """Una prenda creada en el móvil (sync push) llega al servidor y se recupera por pull."""
    async with await _client() as client:
        token = await _token(client)
        auth = {"Authorization": f"Bearer {token}"}
        push = await client.post(
            "/api/v1/sync/push",
            headers=auth,
            json={
                "changes": [
                    {
                        "entity": "garment",
                        "id": "019f6868-9a2c-75b7-8cf1-36e2316aed99",
                        "op": "upsert",
                        "version": 1,
                        "updated_at": "2026-07-25T10:00:00Z",
                        "data": {
                            "category": "arriba",
                            "name": "Camisa azul",
                            "color": "azul",
                            "styles": "formal,ejecutivo",
                        },
                    }
                ]
            },
        )
        assert push.status_code == 200, push.text
        assert push.json()["results"][0]["status"] == "applied"

        pull = await client.get("/api/v1/sync/pull", headers=auth)
    assert pull.status_code == 200
    entries = [c for c in pull.json()["changes"] if c["entity"] == "garment"]
    assert len(entries) == 1
    assert entries[0]["data"] == {
        "category": "arriba",
        "name": "Camisa azul",
        "color": "azul",
        "styles": "formal,ejecutivo",
    }
