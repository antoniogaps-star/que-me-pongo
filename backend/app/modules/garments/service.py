"""Lógica de prendas. Los estilos se guardan como CSV.

DEFENSA EN PROFUNDIDAD: cada consulta filtra por `tenant_id` explícitamente, además
de la política RLS de Postgres. No basta con RLS: hay proveedores (Neon, entre otros)
donde el rol de la base de datos **ignora** las políticas por tener privilegios
elevados, y entonces un usuario vería el clóset de otro. El filtro en código protege
aunque la base falle en aplicarlas.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.garments.models import Garment
from app.shared.errors import api_error


def styles_to_csv(styles: list[str]) -> str:
    return ",".join(styles)


def styles_from_csv(csv: str) -> list[str]:
    return [s for s in csv.split(",") if s]


async def create_garment(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    category: str,
    name: str,
    color: str | None,
    styles: list[str],
    formality: int = 5,
    season: str = "todo",
) -> Garment:
    garment = Garment(
        tenant_id=tenant_id,
        category=category,
        name=name,
        color=color,
        styles=styles_to_csv(styles),
        formality=formality,
        season=season,
    )
    session.add(garment)
    await session.flush()
    return garment


async def list_garments(session: AsyncSession, tenant_id: UUID) -> list[Garment]:
    rows = await session.execute(
        select(Garment)
        .where(Garment.tenant_id == tenant_id, Garment.is_deleted.is_(False))
        .order_by(Garment.name)
    )
    return list(rows.scalars().all())


async def get_garment(
    session: AsyncSession, garment_id: UUID, tenant_id: UUID
) -> Garment | None:
    """Busca una prenda SOLO dentro del clóset del tenant indicado."""
    rows = await session.execute(
        select(Garment).where(Garment.id == garment_id, Garment.tenant_id == tenant_id)
    )
    return rows.scalars().first()


async def delete_garment(session: AsyncSession, garment_id: UUID, tenant_id: UUID) -> None:
    garment = await get_garment(session, garment_id, tenant_id)
    if garment is None or garment.is_deleted:
        raise api_error(404, "GARMENT_NOT_FOUND", "Prenda no encontrada")
    garment.is_deleted = True
    garment.version += 1
    await session.flush()
