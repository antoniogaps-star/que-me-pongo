"""Prendas del clóset: alta, lista, y aislamiento entre usuarios (RLS)."""

from httpx import ASGITransport, AsyncClient

from app.main import app


async def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _register(client: AsyncClient, slug: str) -> dict[str, str]:
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "company_name": slug,
            "company_slug": slug,
            "email": f"dueno@{slug}.com",
            "password": "password123",
        },
    )
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def test_alta_y_lista_de_prendas() -> None:
    async with await _client() as client:
        auth = await _register(client, "closet-uno")
        r = await client.post(
            "/api/v1/garments",
            json={
                "category": "arriba",
                "name": "Camisa blanca",
                "color": "blanco",
                "styles": ["elegante", "ejecutivo"],
                "formality": 8,
                "season": "todo",
            },
            headers=auth,
        )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["styles"] == ["elegante", "ejecutivo"]
        assert body["category"] == "arriba"
        assert body["formality"] == 8

        lst = await client.get("/api/v1/garments", headers=auth)
    assert lst.status_code == 200
    assert len(lst.json()) == 1


async def test_prendas_aisladas_por_usuario() -> None:
    """Cada clóset es privado: un usuario no ve las prendas de otro (RLS)."""
    async with await _client() as client:
        auth_a = await _register(client, "closet-a")
        auth_b = await _register(client, "closet-b")
        await client.post(
            "/api/v1/garments",
            json={
                "category": "calzado",
                "name": "Tenis negros",
                "styles": ["casual", "streetwear"],
            },
            headers=auth_a,
        )
        vista_b = await client.get("/api/v1/garments", headers=auth_b)
    assert vista_b.status_code == 200
    assert vista_b.json() == []
