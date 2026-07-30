"""Respaldo de las fotos del clóset.

Lo que se cuida aquí, además de que funcione: **la foto de tu ropa es tuya**. Un id de
prenda no puede alcanzar para que otra persona vea o pise tu imagen.
"""

from httpx import ASGITransport, AsyncClient

from app.main import app

# Un PNG de 1x1 real: sirve para probar el camino completo sin cargar un archivo grande.
PNG_1x1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c6360000002000100ffff03000006000557bfabd400"
    "00000049454e44ae426082"
)


async def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _cuenta(client: AsyncClient, slug: str) -> str:
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
    return r.json()["access_token"]


async def _prenda(client: AsyncClient, auth: dict[str, str], nombre: str) -> str:
    r = await client.post(
        "/api/v1/garments",
        headers=auth,
        json={"category": "arriba", "name": nombre},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _archivo() -> dict[str, tuple[str, bytes, str]]:
    return {"archivo": ("prenda.png", PNG_1x1, "image/png")}


async def test_la_foto_sube_y_se_puede_recuperar() -> None:
    """El caso que da sentido a todo: cambias de teléfono y tu ropa sigue con foto."""
    async with await _client() as client:
        auth = {"Authorization": f"Bearer {await _cuenta(client, 'closet-uno')}"}
        prenda = await _prenda(client, auth, "Camisa azul")

        subida = await client.put(
            f"/api/v1/garments/{prenda}/foto", headers=auth, files=_archivo()
        )
        assert subida.status_code == 204, subida.text

        bajada = await client.get(f"/api/v1/garments/{prenda}/foto", headers=auth)

    assert bajada.status_code == 200
    assert bajada.content == PNG_1x1
    assert bajada.headers["content-type"] == "image/png"


async def test_se_puede_saber_que_prendas_ya_tienen_foto() -> None:
    async with await _client() as client:
        auth = {"Authorization": f"Bearer {await _cuenta(client, 'closet-uno')}"}
        con = await _prenda(client, auth, "Camisa azul")
        sin = await _prenda(client, auth, "Pantalón")
        await client.put(f"/api/v1/garments/{con}/foto", headers=auth, files=_archivo())

        lista = await client.get("/api/v1/garments/fotos", headers=auth)

    assert lista.status_code == 200, lista.text
    assert lista.json() == [con]
    assert sin not in lista.json()


async def test_volver_a_subir_reemplaza_la_anterior() -> None:
    async with await _client() as client:
        auth = {"Authorization": f"Bearer {await _cuenta(client, 'closet-uno')}"}
        prenda = await _prenda(client, auth, "Camisa azul")
        await client.put(f"/api/v1/garments/{prenda}/foto", headers=auth, files=_archivo())

        otra = {"archivo": ("otra.png", PNG_1x1 + b"\x00", "image/png")}
        await client.put(f"/api/v1/garments/{prenda}/foto", headers=auth, files=otra)

        bajada = await client.get(f"/api/v1/garments/{prenda}/foto", headers=auth)
        lista = await client.get("/api/v1/garments/fotos", headers=auth)

    assert bajada.content == PNG_1x1 + b"\x00"
    # Sigue habiendo UNA foto, no dos.
    assert lista.json() == [prenda]


async def test_no_se_aceptan_archivos_que_no_son_imagen() -> None:
    async with await _client() as client:
        auth = {"Authorization": f"Bearer {await _cuenta(client, 'closet-uno')}"}
        prenda = await _prenda(client, auth, "Camisa azul")
        r = await client.put(
            f"/api/v1/garments/{prenda}/foto",
            headers=auth,
            files={"archivo": ("virus.pdf", b"%PDF-1.4", "application/pdf")},
        )
    assert r.status_code == 415
    assert r.json()["error"]["code"] == "UNSUPPORTED_IMAGE"


async def test_no_se_acepta_una_imagen_gigante() -> None:
    """Sin tope, una sola subida podría llenar la base."""
    async with await _client() as client:
        auth = {"Authorization": f"Bearer {await _cuenta(client, 'closet-uno')}"}
        prenda = await _prenda(client, auth, "Camisa azul")
        enorme = b"\x00" * (3 * 1024 * 1024 + 1)
        r = await client.put(
            f"/api/v1/garments/{prenda}/foto",
            headers=auth,
            files={"archivo": ("grande.jpg", enorme, "image/jpeg")},
        )
    assert r.status_code == 413
    assert r.json()["error"]["code"] == "IMAGE_TOO_LARGE"


async def test_al_borrar_la_prenda_se_va_su_foto() -> None:
    async with await _client() as client:
        auth = {"Authorization": f"Bearer {await _cuenta(client, 'closet-uno')}"}
        prenda = await _prenda(client, auth, "Camisa azul")
        await client.put(f"/api/v1/garments/{prenda}/foto", headers=auth, files=_archivo())

        await client.delete(f"/api/v1/garments/{prenda}", headers=auth)
        lista = await client.get("/api/v1/garments/fotos", headers=auth)
        bajada = await client.get(f"/api/v1/garments/{prenda}/foto", headers=auth)

    assert lista.json() == []
    assert bajada.status_code == 404


# ── GUARDIÁN: la ropa de otro no se ve ni se toca ────────────


async def test_no_se_puede_ver_la_foto_de_otro_closet() -> None:
    async with await _client() as client:
        mia = {"Authorization": f"Bearer {await _cuenta(client, 'closet-uno')}"}
        prenda = await _prenda(client, mia, "Camisa azul")
        await client.put(f"/api/v1/garments/{prenda}/foto", headers=mia, files=_archivo())

        ajena = {"Authorization": f"Bearer {await _cuenta(client, 'closet-dos')}"}
        intento = await client.get(f"/api/v1/garments/{prenda}/foto", headers=ajena)

    assert intento.status_code == 404, "¡se filtró la foto de otro clóset!"


async def test_no_se_puede_pisar_la_foto_de_otro_closet() -> None:
    async with await _client() as client:
        mia = {"Authorization": f"Bearer {await _cuenta(client, 'closet-uno')}"}
        prenda = await _prenda(client, mia, "Camisa azul")
        await client.put(f"/api/v1/garments/{prenda}/foto", headers=mia, files=_archivo())

        ajena = {"Authorization": f"Bearer {await _cuenta(client, 'closet-dos')}"}
        intento = await client.put(
            f"/api/v1/garments/{prenda}/foto",
            headers=ajena,
            files={"archivo": ("suya.png", b"otra cosa", "image/png")},
        )
        assert intento.status_code == 404

        # Y la mía quedó intacta.
        bajada = await client.get(f"/api/v1/garments/{prenda}/foto", headers=mia)

    assert bajada.content == PNG_1x1


async def test_la_lista_de_fotos_no_mezcla_closets() -> None:
    async with await _client() as client:
        mia = {"Authorization": f"Bearer {await _cuenta(client, 'closet-uno')}"}
        prenda = await _prenda(client, mia, "Camisa azul")
        await client.put(f"/api/v1/garments/{prenda}/foto", headers=mia, files=_archivo())

        ajena = {"Authorization": f"Bearer {await _cuenta(client, 'closet-dos')}"}
        suya = await client.get("/api/v1/garments/fotos", headers=ajena)

    assert suya.json() == []


async def test_la_foto_pide_sesion() -> None:
    async with await _client() as client:
        auth = {"Authorization": f"Bearer {await _cuenta(client, 'closet-uno')}"}
        prenda = await _prenda(client, auth, "Camisa azul")
        await client.put(f"/api/v1/garments/{prenda}/foto", headers=auth, files=_archivo())

        sin_sesion = await client.get(f"/api/v1/garments/{prenda}/foto")

    assert sin_sesion.status_code in (401, 403)


async def test_borrar_la_prenda_por_sincronizacion_tambien_borra_su_foto() -> None:
    """El celular borra prendas por sync, no por la API REST.

    Sin esto, cada prenda borrada desde el teléfono dejaba su imagen huérfana en la
    base ocupando espacio para siempre.
    """
    from datetime import UTC, datetime

    async with await _client() as client:
        auth = {"Authorization": f"Bearer {await _cuenta(client, 'closet-uno')}"}
        prenda = await _prenda(client, auth, "Camisa azul")
        await client.put(f"/api/v1/garments/{prenda}/foto", headers=auth, files=_archivo())
        assert (await client.get("/api/v1/garments/fotos", headers=auth)).json() == [prenda]

        await client.post(
            "/api/v1/sync/push",
            headers=auth,
            json={
                "changes": [
                    {
                        "entity": "garment",
                        "id": prenda,
                        "op": "delete",
                        "version": 2,
                        "updated_at": datetime.now(UTC).isoformat(),
                        "data": {},
                    }
                ]
            },
        )
        lista = await client.get("/api/v1/garments/fotos", headers=auth)

    assert lista.json() == []
