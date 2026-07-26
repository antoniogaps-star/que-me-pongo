"""Lógica de favoritos y perfil de estilo.

DEFENSA EN PROFUNDIDAD: cada consulta filtra por `tenant_id` explícitamente, además
de la política RLS de Postgres. No basta con RLS: hay proveedores donde el rol de la
base **ignora** las políticas por tener privilegios elevados.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.outfits.models import Outfit, StyleProfile
from app.shared.errors import api_error


def ids_to_csv(ids: list[UUID]) -> str:
    return ",".join(str(i) for i in ids)


def ids_from_csv(csv: str) -> list[UUID]:
    return [UUID(i) for i in csv.split(",") if i]


def csv_to_list(csv: str) -> list[str]:
    return [s for s in csv.split(",") if s]


async def save_outfit(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    garment_ids: list[UUID],
    occasion: str,
    projection: str,
    explanation: str,
) -> Outfit:
    outfit = Outfit(
        tenant_id=tenant_id,
        garment_ids=ids_to_csv(garment_ids),
        occasion=occasion,
        projection=projection,
        explanation=explanation,
    )
    session.add(outfit)
    await session.flush()
    return outfit


async def list_outfits(session: AsyncSession, tenant_id: UUID) -> list[Outfit]:
    rows = await session.execute(
        select(Outfit)
        .where(Outfit.tenant_id == tenant_id, Outfit.is_deleted.is_(False))
        .order_by(Outfit.created_at.desc())
    )
    return list(rows.scalars().all())


async def delete_outfit(session: AsyncSession, outfit_id: UUID, tenant_id: UUID) -> None:
    rows = await session.execute(
        select(Outfit).where(Outfit.id == outfit_id, Outfit.tenant_id == tenant_id)
    )
    outfit = rows.scalars().first()
    if outfit is None or outfit.is_deleted:
        raise api_error(404, "OUTFIT_NOT_FOUND", "Outfit no encontrado")
    outfit.is_deleted = True
    outfit.version += 1
    await session.flush()


async def get_profile(session: AsyncSession, tenant_id: UUID) -> StyleProfile | None:
    rows = await session.execute(
        select(StyleProfile).where(StyleProfile.tenant_id == tenant_id)
    )
    return rows.scalars().first()


async def upsert_profile(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    styles: list[str],
    avoid_colors: list[str],
) -> StyleProfile:
    profile = await get_profile(session, tenant_id)
    if profile is None:
        profile = StyleProfile(tenant_id=tenant_id)
        session.add(profile)
    profile.styles = ",".join(styles)
    profile.avoid_colors = ",".join(avoid_colors)
    await session.flush()
    return profile
