"""Endpoints REST de favoritos y perfil de estilo."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.modules.billing.deps import require_active_subscription
from app.modules.outfits import service
from app.modules.outfits.schemas import (
    OutfitCreate,
    OutfitRead,
    StyleProfileRead,
    StyleProfileUpdate,
)
from app.shared.deps import Claims, TenantSession

router = APIRouter(
    prefix="/outfits",
    tags=["outfits"],
    dependencies=[Depends(require_active_subscription)],
)

profile_router = APIRouter(
    prefix="/style-profile",
    tags=["outfits"],
    dependencies=[Depends(require_active_subscription)],
)


def _read(o: Any) -> dict[str, Any]:
    return {
        "id": o.id,
        "garment_ids": service.ids_from_csv(o.garment_ids),
        "occasion": o.occasion,
        "projection": o.projection,
        "explanation": o.explanation,
    }


@router.get("", response_model=list[OutfitRead])
async def list_outfits(session: TenantSession, claims: Claims) -> list[dict[str, Any]]:
    return [_read(o) for o in await service.list_outfits(session)]


@router.post("", response_model=OutfitRead, status_code=status.HTTP_201_CREATED)
async def save_outfit(
    data: OutfitCreate, session: TenantSession, claims: Claims
) -> dict[str, Any]:
    outfit = await service.save_outfit(
        session,
        tenant_id=UUID(claims["tenant_id"]),
        garment_ids=list(data.garment_ids),
        occasion=data.occasion,
        projection=data.projection,
        explanation=data.explanation,
    )
    return _read(outfit)


@router.delete("/{outfit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_outfit(
    outfit_id: UUID, session: TenantSession, claims: Claims
) -> None:
    await service.delete_outfit(session, outfit_id)


@profile_router.get("", response_model=StyleProfileRead)
async def read_profile(session: TenantSession, claims: Claims) -> dict[str, Any]:
    profile = await service.get_profile(session, UUID(claims["tenant_id"]))
    if profile is None:
        return {"styles": [], "avoid_colors": []}
    return {
        "styles": service.csv_to_list(profile.styles),
        "avoid_colors": service.csv_to_list(profile.avoid_colors),
    }


@profile_router.put("", response_model=StyleProfileRead)
async def update_profile(
    data: StyleProfileUpdate, session: TenantSession, claims: Claims
) -> dict[str, Any]:
    profile = await service.upsert_profile(
        session,
        tenant_id=UUID(claims["tenant_id"]),
        styles=list(data.styles),
        avoid_colors=list(data.avoid_colors),
    )
    return {
        "styles": service.csv_to_list(profile.styles),
        "avoid_colors": service.csv_to_list(profile.avoid_colors),
    }
