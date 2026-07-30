"""El aislamiento debe aguantar AUNQUE la base no aplique RLS.

Por qué existe esta prueba: en producción (Neon) el rol de la base tiene privilegios
elevados y **ignora** las políticas RLS. Con el aislamiento delegado solo a Postgres,
un usuario veía el clóset de otro. Pasó de verdad, en producción.

Aquí se reproduce ese entorno a propósito: se quita el FORCE de las políticas, con lo
que el rol dueño deja de estar sujeto a ellas — exactamente lo que pasa en Neon. Luego
se comprueba que las consultas del código siguen filtrando por tenant. Si alguien vuelve
a escribir una consulta sin `WHERE tenant_id`, esta prueba falla.
"""

import pytest
from sqlalchemy import text

# Importar el modelo de tenants completa el mapeo (las prendas lo referencian).
import app.modules.tenants.models  # noqa: F401
from app.modules.garments import service as garments
from app.modules.outfits import service as outfits
from app.sync import service as sync
from app.sync.schemas import Change, PushRequest

_TABLAS = ("garments", "outfits", "garment_photos")


@pytest.fixture
async def base_sin_aislamiento(owner_sessions):
    """Deja la base como Neon: las políticas existen pero NO se aplican a este rol."""
    async with owner_sessions() as s:
        for t in _TABLAS:
            await s.execute(text(f"ALTER TABLE {t} NO FORCE ROW LEVEL SECURITY"))
        await s.commit()
    yield
    async with owner_sessions() as s:
        for t in _TABLAS:
            await s.execute(text(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY"))
        await s.commit()


@pytest.fixture
async def dos_closets(base_sin_aislamiento, owner_sessions):
    """Dos tenants con una prenda cada uno. Devuelve (tenant_a, tenant_b, id_prenda_a)."""
    from uuid import uuid4

    tenant_a, tenant_b = uuid4(), uuid4()
    async with owner_sessions() as s:
        for t, nombre in ((tenant_a, "Empresa A"), (tenant_b, "Empresa B")):
            await s.execute(
                text("INSERT INTO tenants (id, name, slug) VALUES (:i, :n, :s)"),
                {"i": t, "n": nombre, "s": str(t)[:8]},
            )
        await s.commit()

    async with owner_sessions() as s:
        prenda_a = await garments.create_garment(
            s, tenant_id=tenant_a, category="arriba", name="Camisa de A", color=None, styles=[]
        )
        await garments.create_garment(
            s, tenant_id=tenant_b, category="arriba", name="Camisa de B", color=None, styles=[]
        )
        await s.commit()
        id_a = prenda_a.id

    return tenant_a, tenant_b, id_a


async def test_listar_prendas_no_filtra_de_mas(dos_closets, owner_sessions) -> None:
    """Cada quien ve SOLO su ropa, aunque la base no esté filtrando."""
    tenant_a, tenant_b, _ = dos_closets
    async with owner_sessions() as s:
        de_a = [g.name for g in await garments.list_garments(s, tenant_a)]
        de_b = [g.name for g in await garments.list_garments(s, tenant_b)]
    assert de_a == ["Camisa de A"]
    assert de_b == ["Camisa de B"]


async def test_no_se_puede_borrar_la_prenda_de_otro(dos_closets, owner_sessions) -> None:
    """B intenta borrar una prenda de A por su id: debe responder 'no encontrada'."""
    _, tenant_b, id_de_a = dos_closets
    async with owner_sessions() as s:
        with pytest.raises(Exception) as fallo:
            await garments.delete_garment(s, id_de_a, tenant_b)
    assert "GARMENT_NOT_FOUND" in str(fallo.value)


async def test_el_pull_no_arrastra_el_closet_ajeno(dos_closets, owner_sessions) -> None:
    tenant_a, tenant_b, _ = dos_closets
    async with owner_sessions() as s:
        respuesta = await sync.pull(s, tenant_b, None)
    nombres = [c.data["name"] for c in respuesta.changes if c.entity == "garment"]
    assert nombres == ["Camisa de B"]


async def test_el_push_no_sobrescribe_la_prenda_de_otro(dos_closets, owner_sessions) -> None:
    """Lo más peligroso: B empuja un cambio con el id de A. No debe pisarle su prenda."""
    tenant_a, tenant_b, id_de_a = dos_closets
    from datetime import UTC, datetime

    async with owner_sessions() as s:
        respuesta = await sync.push(
            s,
            tenant_b,
            PushRequest(
                changes=[
                    Change(
                        entity="garment",
                        id=id_de_a,
                        op="upsert",
                        version=99,
                        updated_at=datetime.now(UTC),
                        data={"name": "SECUESTRADA", "category": "arriba"},
                    )
                ]
            ),
        )
        await s.commit()

    # Se rechaza con un estado claro, no con un error del servidor.
    assert respuesta.results[0].status == "rejected"

    async with owner_sessions() as s:
        de_a = [g.name for g in await garments.list_garments(s, tenant_a)]
    assert de_a == ["Camisa de A"], "un tenant sobrescribió la prenda de otro"


async def test_favoritos_tambien_quedan_aislados(dos_closets, owner_sessions) -> None:
    tenant_a, tenant_b, _ = dos_closets
    async with owner_sessions() as s:
        await outfits.save_outfit(
            s, tenant_id=tenant_a, garment_ids=[], occasion="cita", projection="", explanation=""
        )
        await s.commit()

    async with owner_sessions() as s:
        assert await outfits.list_outfits(s, tenant_b) == []
        assert len(await outfits.list_outfits(s, tenant_a)) == 1


async def test_la_foto_de_otro_no_se_alcanza_sin_rls(dos_closets, owner_sessions) -> None:
    """Aunque la base no filtre, la foto de la prenda de A no es visible para B.

    Es el mismo escenario de Neon: si el aislamiento dependiera solo de la base, aquí se
    filtraría la imagen de la ropa de otra persona.
    """
    from app.modules.garments import photos

    tenant_a, tenant_b, id_de_a = dos_closets

    async with owner_sessions() as s:
        await photos.guardar(
            s,
            garment_id=id_de_a,
            tenant_id=tenant_a,
            data=b"foto de A",
            content_type="image/jpeg",
        )
        await s.commit()

    async with owner_sessions() as s:
        assert await photos.obtener(s, id_de_a, tenant_b) is None
        assert await photos.con_foto(s, tenant_b) == set()
        # Y para su dueño sí está.
        mia = await photos.obtener(s, id_de_a, tenant_a)
        assert mia is not None and mia.data == b"foto de A"


async def test_no_se_puede_respaldar_sobre_la_prenda_de_otro(
    dos_closets, owner_sessions
) -> None:
    import pytest as _pytest

    from app.modules.garments import photos

    _, tenant_b, id_de_a = dos_closets
    async with owner_sessions() as s:
        with _pytest.raises(Exception) as fallo:
            await photos.guardar(
                s,
                garment_id=id_de_a,
                tenant_id=tenant_b,
                data=b"secuestrada",
                content_type="image/jpeg",
            )
    assert "GARMENT_NOT_FOUND" in str(fallo.value)

