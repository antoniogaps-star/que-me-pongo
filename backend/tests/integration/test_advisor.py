"""El asesor de punta a punta: clóset real → recomendación → favorito.

Sin ANTHROPIC_API_KEY en pruebas, el endpoint debe caer a reglas locales y responder
igual: eso es justo lo que garantiza que la app nunca se quede muda.
"""

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


async def _add(client: AsyncClient, auth: dict[str, str], **prenda: object) -> str:
    r = await client.post("/api/v1/garments", json=prenda, headers=auth)
    assert r.status_code == 201, r.text
    return str(r.json()["id"])


async def _closet_basico(client: AsyncClient, auth: dict[str, str]) -> dict[str, str]:
    return {
        "playera": await _add(
            client, auth, category="arriba", name="Playera gris", color="gris",
            styles=["casual"], formality=3,
        ),
        "camisa": await _add(
            client, auth, category="arriba", name="Camisa blanca", color="blanco",
            styles=["elegante"], formality=9,
        ),
        "jeans": await _add(
            client, auth, category="abajo", name="Jeans", color="azul",
            styles=["casual"], formality=4,
        ),
        "vestir": await _add(
            client, auth, category="abajo", name="Pantalón de vestir", color="negro",
            styles=["elegante"], formality=9,
        ),
        "tenis": await _add(
            client, auth, category="calzado", name="Tenis", color="blanco",
            styles=["deportivo"], formality=3,
        ),
        "zapatos": await _add(
            client, auth, category="calzado", name="Zapatos", color="negro",
            styles=["elegante"], formality=9,
        ),
    }


async def test_closet_vacio_invita_a_empezar() -> None:
    """El mensaje debe guiar, no regañar."""
    async with await _client() as client:
        auth = await _register(client, "closet-vacio")
        r = await client.post("/api/v1/advisor/recommend", json={}, headers=auth)
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "EMPTY_CLOSET"


async def test_recomienda_conjunto_completo_con_explicacion() -> None:
    async with await _client() as client:
        auth = await _register(client, "closet-asesor")
        ids = await _closet_basico(client, auth)
        r = await client.post(
            "/api/v1/advisor/recommend",
            json={"occasion": "evento formal", "projection": "Elegante"},
            headers=auth,
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["outfits"]) >= 1
    outfit = body["outfits"][0]
    # Sin llave de IA en pruebas: debe venir de las reglas y elegir lo formal.
    assert body["source"] == "reglas"
    assert set(outfit["garment_ids"]) == {ids["camisa"], ids["vestir"], ids["zapatos"]}
    assert outfit["explanation"]
    assert outfit["projected_image"] == "Elegante"


async def test_recomendacion_solo_usa_prendas_propias() -> None:
    """El clóset de uno nunca se mezcla con el de otro (RLS)."""
    async with await _client() as client:
        auth_a = await _register(client, "asesor-a")
        auth_b = await _register(client, "asesor-b")
        ids_a = await _closet_basico(client, auth_a)
        r = await client.post(
            "/api/v1/advisor/recommend", json={"occasion": "dia normal"}, headers=auth_b
        )
        assert r.status_code == 400  # el clóset de B está vacío

        r_a = await client.post(
            "/api/v1/advisor/recommend", json={"occasion": "dia normal"}, headers=auth_a
        )
    assert r_a.status_code == 200
    assert set(r_a.json()["outfits"][0]["garment_ids"]) <= set(ids_a.values())


async def test_guardar_y_listar_favorito() -> None:
    async with await _client() as client:
        auth = await _register(client, "favoritos")
        ids = await _closet_basico(client, auth)
        guardar = await client.post(
            "/api/v1/outfits",
            json={
                "garment_ids": [ids["camisa"], ids["vestir"], ids["zapatos"]],
                "occasion": "evento formal",
                "projection": "Elegante",
                "explanation": "Combinación sobria que proyecta seguridad.",
            },
            headers=auth,
        )
        assert guardar.status_code == 201, guardar.text
        lista = await client.get("/api/v1/outfits", headers=auth)
    assert lista.status_code == 200
    assert len(lista.json()) == 1
    assert lista.json()[0]["occasion"] == "evento formal"


async def test_perfil_de_estilo_se_guarda_y_se_lee() -> None:
    async with await _client() as client:
        auth = await _register(client, "perfil-estilo")
        vacio = await client.get("/api/v1/style-profile", headers=auth)
        assert vacio.json() == {"styles": [], "avoid_colors": []}

        guardado = await client.put(
            "/api/v1/style-profile",
            json={"styles": ["moderno", "casual"], "avoid_colors": ["amarillo"]},
            headers=auth,
        )
        assert guardado.status_code == 200
        leido = await client.get("/api/v1/style-profile", headers=auth)
    assert leido.json()["styles"] == ["moderno", "casual"]
    assert leido.json()["avoid_colors"] == ["amarillo"]


async def test_clasificar_sin_llave_responde_claro() -> None:
    """Sin IA no se puede leer una foto: el mensaje debe decir qué hacer."""
    async with await _client() as client:
        auth = await _register(client, "clasificar")
        r = await client.post(
            "/api/v1/advisor/classify",
            json={"image_base64": "Zm90bw=="},
            headers=auth,
        )
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "ADVISOR_UNAVAILABLE"
