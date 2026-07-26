"""Lógica de prendas (tenant-scoped por RLS). Los estilos se guardan como CSV."""

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
) -> Garment:
    garment = Garment(
        tenant_id=tenant_id,
        category=category,
        name=name,
        color=color,
        styles=styles_to_csv(styles),
    )
    session.add(garment)
    await session.flush()
    return garment


async def list_garments(session: AsyncSession) -> list[Garment]:
    rows = await session.execute(
        select(Garment).where(Garment.is_deleted.is_(False)).order_by(Garment.name)
    )
    return list(rows.scalars().all())


async def delete_garment(session: AsyncSession, garment_id: UUID) -> None:
    garment = await session.get(Garment, garment_id)
    if garment is None or garment.is_deleted:
        raise api_error(404, "GARMENT_NOT_FOUND", "Prenda no encontrada")
    garment.is_deleted = True
    garment.version += 1
    await session.flush()
