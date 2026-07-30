"""Endpoints REST de prendas, incluida la foto respaldada de cada una."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Response, UploadFile, status

from app.modules.billing.deps import require_active_subscription
from app.modules.garments import photos, service
from app.modules.garments.schemas import GarmentCreate, GarmentRead
from app.shared.deps import Claims, TenantSession
from app.shared.errors import api_error

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
    tenant_id = UUID(claims["tenant_id"])
    await service.delete_garment(session, garment_id, tenant_id)
    # La foto se va con la prenda: ya no sirve de nada y ocupa espacio.
    await photos.borrar(session, garment_id, tenant_id)


# ── La foto de cada prenda ───────────────────────────────────


@router.get("/fotos", response_model=list[UUID])
async def garments_with_photo(session: TenantSession, claims: Claims) -> list[UUID]:
    """Qué prendas ya tienen foto respaldada.

    El móvil lo consulta para saber qué le falta subir y qué puede bajar, en una sola
    petición en vez de una por prenda.
    """
    return sorted(await photos.con_foto(session, UUID(claims["tenant_id"])))


@router.put("/{garment_id}/foto", status_code=status.HTTP_204_NO_CONTENT)
async def upload_photo(
    garment_id: UUID,
    session: TenantSession,
    claims: Claims,
    archivo: Annotated[UploadFile, File()],
) -> None:
    """Respalda la foto de una prenda. Reemplaza la anterior si ya había."""
    contenido = await archivo.read()
    await photos.guardar(
        session,
        garment_id=garment_id,
        tenant_id=UUID(claims["tenant_id"]),
        data=contenido,
        content_type=archivo.content_type or "image/jpeg",
    )


@router.get("/{garment_id}/foto")
async def download_photo(
    garment_id: UUID, session: TenantSession, claims: Claims
) -> Response:
    foto = await photos.obtener(session, garment_id, UUID(claims["tenant_id"]))
    if foto is None:
        raise api_error(404, "PHOTO_NOT_FOUND", "Esa prenda no tiene foto respaldada")
    return Response(
        content=foto.data,
        media_type=foto.content_type,
        # Puede cachearse un buen rato: la foto de una prenda no cambia sola.
        headers={"Cache-Control": "private, max-age=86400"},
    )


@router.delete("/{garment_id}/foto", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(
    garment_id: UUID, session: TenantSession, claims: Claims
) -> None:
    await photos.borrar(session, garment_id, UUID(claims["tenant_id"]))
