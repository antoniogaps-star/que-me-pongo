"""Motor de sincronización. La prenda es last-write-wins con soporte de borrado.

pull devuelve, por entidad, las filas con `updated_at` posterior al cursor del cliente
(incluidos tombstones), y un nuevo cursor.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.garments.models import Garment
from app.modules.outfits.models import Outfit
from app.sync.schemas import Change, ChangeResult, PullResponse, PushRequest, PushResponse

SUPPORTED_ENTITIES = {"garment", "outfit"}


def _garment_data(g: Garment) -> dict[str, Any]:
    return {
        "category": g.category,
        "name": g.name,
        "color": g.color,
        "styles": g.styles,
        "formality": g.formality,
        "season": g.season,
    }


def _outfit_data(o: Outfit) -> dict[str, Any]:
    return {
        "garment_ids": o.garment_ids,
        "occasion": o.occasion,
        "projection": o.projection,
        "explanation": o.explanation,
    }


async def push(session: AsyncSession, tenant_id: UUID, payload: PushRequest) -> PushResponse:
    results: list[ChangeResult] = []
    for change in payload.changes:
        if change.entity == "garment":
            results.append(await _push_garment(session, tenant_id, change))
        elif change.entity == "outfit":
            results.append(await _push_outfit(session, tenant_id, change))
        else:
            results.append(
                ChangeResult(id=change.id, entity=change.entity, status="unsupported")
            )
    return PushResponse(results=results)


async def _push_garment(session: AsyncSession, tenant_id: UUID, ch: Change) -> ChangeResult:
    data = ch.data or {}
    existing = await session.get(Garment, ch.id)
    if existing is None:
        session.add(
            Garment(
                id=ch.id,
                tenant_id=tenant_id,
                category=data.get("category", "arriba"),
                name=data.get("name", ""),
                color=data.get("color"),
                styles=data.get("styles", ""),
                formality=data.get("formality", 5),
                season=data.get("season", "todo"),
                is_deleted=(ch.op == "delete"),
                version=ch.version,
                updated_at=ch.updated_at,
            )
        )
        await session.flush()
        return ChangeResult(
            id=ch.id, entity="garment", status="applied", server_version=ch.version
        )

    if ch.updated_at < existing.updated_at:
        return ChangeResult(
            id=ch.id, entity="garment", status="conflict", server_version=existing.version
        )
    existing.category = data.get("category", existing.category)
    existing.name = data.get("name", existing.name)
    existing.color = data.get("color", existing.color)
    existing.styles = data.get("styles", existing.styles)
    existing.formality = data.get("formality", existing.formality)
    existing.season = data.get("season", existing.season)
    existing.is_deleted = ch.op == "delete"
    existing.version = ch.version
    existing.updated_at = ch.updated_at
    await session.flush()
    return ChangeResult(
        id=ch.id, entity="garment", status="applied", server_version=existing.version
    )


async def _push_outfit(session: AsyncSession, tenant_id: UUID, ch: Change) -> ChangeResult:
    data = ch.data or {}
    existing = await session.get(Outfit, ch.id)
    if existing is None:
        session.add(
            Outfit(
                id=ch.id,
                tenant_id=tenant_id,
                garment_ids=data.get("garment_ids", ""),
                occasion=data.get("occasion", ""),
                projection=data.get("projection", ""),
                explanation=data.get("explanation", ""),
                is_deleted=(ch.op == "delete"),
                version=ch.version,
                updated_at=ch.updated_at,
            )
        )
        await session.flush()
        return ChangeResult(
            id=ch.id, entity="outfit", status="applied", server_version=ch.version
        )

    if ch.updated_at < existing.updated_at:
        return ChangeResult(
            id=ch.id, entity="outfit", status="conflict", server_version=existing.version
        )
    existing.garment_ids = data.get("garment_ids", existing.garment_ids)
    existing.occasion = data.get("occasion", existing.occasion)
    existing.projection = data.get("projection", existing.projection)
    existing.explanation = data.get("explanation", existing.explanation)
    existing.is_deleted = ch.op == "delete"
    existing.version = ch.version
    existing.updated_at = ch.updated_at
    await session.flush()
    return ChangeResult(
        id=ch.id, entity="outfit", status="applied", server_version=existing.version
    )


async def pull(session: AsyncSession, since: str | None) -> PullResponse:
    since_dt = datetime.fromisoformat(since) if since else None
    changes: list[Change] = []
    changes += await _pull(session, "garment", Garment, _garment_data, since_dt)
    changes += await _pull(session, "outfit", Outfit, _outfit_data, since_dt)
    return PullResponse(changes=changes, cursor=datetime.now(UTC).isoformat())


async def _pull(
    session: AsyncSession, name: str, model: Any, data_fn: Any, since_dt: datetime | None
) -> list[Change]:
    query = select(model)
    if since_dt is not None:
        query = query.where(model.updated_at > since_dt)
    rows = (await session.execute(query)).scalars().all()
    return [
        Change(
            entity=name,
            id=row.id,
            op="delete" if row.is_deleted else "upsert",
            version=row.version,
            updated_at=row.updated_at,
            data=data_fn(row),
        )
        for row in rows
    ]
