"""Endpoints REST de prendas."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.modules.billing.deps import require_active_subscription
from app.modules.garments import service
from app.modules.garments.schemas import GarmentCreate, GarmentRead
from app.shared.deps import Claims, TenantSession

router = APIRouter(
    prefix="/garments",
    tags=["garments"],
    dependencies=[Depends(require_active_subscription)],
)


def _read(g: Any) -> dict[str, Any]:
    return {
        "id": g.id,
        "category": g.category,
        "name": g.name,
        "color": g.color,
        "styles": service.styles_from_csv(g.styles),
        "formality": g.formality,
        "season": g.season,
    }


@router.get("", response_model=list[GarmentRead])
async def list_garments(session: TenantSession, claims: Claims) -> list[dict[str, Any]]:
    tenant_id = UUID(claims["tenant_id"])
    return [_read(g) for g in await service.list_garments(session, tenant_id)]


@router.post("", response_model=GarmentRead, status_code=status.HTTP_201_CREATED)
async def create_garment(
    data: GarmentCreate, session: TenantSession, claims: Claims
) -> dict[str, Any]:
    garment = await service.create_garment(
        session,
        tenant_id=UUID(claims["tenant_id"]),
        category=data.category,
        name=data.name,
        color=data.color,
        styles=list(data.styles),
        formality=data.formality,
        season=data.season,
    )
    return _read(garment)


@router.delete("/{garment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_garment(
    garment_id: UUID, session: TenantSession, claims: Claims
) -> None:
    await service.delete_garment(session, garment_id, UUID(claims["tenant_id"]))
