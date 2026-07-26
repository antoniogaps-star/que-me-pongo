"""Endpoints del asesor de imagen: clasificar una foto y recomendar outfits.

Ambos intentan Claude primero y caen a reglas locales si la IA no está disponible. El campo
`source` de la respuesta dice cuál se usó, para que el móvil pueda ser honesto con el usuario.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends

from app.modules.advisor import claude_client, rules
from app.modules.advisor.schemas import (
    ClassifyRequest,
    ClassifyResponse,
    RecommendRequest,
    RecommendResponse,
)
from app.modules.billing.deps import require_active_subscription
from app.modules.garments import service as garments_service
from app.modules.outfits import service as outfits_service
from app.shared.deps import Claims, TenantSession
from app.shared.errors import api_error

router = APIRouter(
    prefix="/advisor",
    tags=["advisor"],
    dependencies=[Depends(require_active_subscription)],
)


@router.post("/classify", response_model=ClassifyResponse)
async def classify(data: ClassifyRequest, claims: Claims) -> dict[str, Any]:
    """Mira la foto de una prenda y devuelve su ficha para que el usuario la confirme.

    Sin IA no hay nada que adivinar de una imagen: aquí sí respondemos 503 y el móvil
    muestra el formulario manual.
    """
    try:
        return await claude_client.classify_photo(data.image_base64, data.media_type)
    except claude_client.AdvisorUnavailable as exc:
        raise api_error(
            503,
            "ADVISOR_UNAVAILABLE",
            "No pude analizar la foto ahora. Captura los datos a mano y sigue adelante.",
        ) from exc


def _garment_dicts(garments: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": str(g.id),
            "category": g.category,
            "name": g.name,
            "color": g.color,
            "styles": garments_service.styles_from_csv(g.styles),
            "formality": g.formality,
            "season": g.season,
        }
        for g in garments
    ]


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(
    data: RecommendRequest, session: TenantSession, claims: Claims
) -> dict[str, Any]:
    """El botón estrella: ¿qué me pongo?"""
    tenant_id = UUID(claims["tenant_id"])
    garments = _garment_dicts(await garments_service.list_garments(session, tenant_id))
    if not garments:
        raise api_error(
            400,
            "EMPTY_CLOSET",
            "Tu clóset está vacío. Toma una foto de tu primera prenda para empezar.",
        )

    profile = await outfits_service.get_profile(session, tenant_id)
    preferred = outfits_service.csv_to_list(profile.styles) if profile else []
    avoid = outfits_service.csv_to_list(profile.avoid_colors) if profile else []

    # Para el modo sorpresa: qué combinaciones ya guardó, para no repetirlas.
    recent: list[list[str]] = []
    if data.surprise:
        saved = await outfits_service.list_outfits(session, tenant_id)
        recent = [
            [str(i) for i in outfits_service.ids_from_csv(o.garment_ids)] for o in saved[:10]
        ]

    valid_ids = {g["id"] for g in garments}
    try:
        suggestions = await claude_client.recommend(
            garments,
            occasion=data.occasion,
            projection=data.projection,
            temperature_c=data.temperature_c,
            preferred_styles=preferred,
            avoid_colors=avoid,
            recent_combos=recent,
            anchor_garment_id=str(data.with_garment_id) if data.with_garment_id else None,
            surprise=data.surprise,
            count=data.count,
        )
        # Red de seguridad: la IA solo puede usar prendas que existen en ESTE clóset.
        clean = [
            {
                "garment_ids": [i for i in s.get("garment_ids", []) if i in valid_ids],
                "explanation": s.get("explanation", ""),
                "projected_image": s.get("projected_image", ""),
            }
            for s in suggestions
        ]
        clean = [s for s in clean if s["garment_ids"]]
        if clean:
            return {"outfits": clean, "source": "claude"}
    except claude_client.AdvisorUnavailable:
        pass  # Sin IA no se cae la app: seguimos con reglas locales.

    fallback = rules.build_outfit(
        garments,
        occasion=data.occasion,
        projection=data.projection,
        temperature_c=data.temperature_c,
    )
    if fallback is None:
        raise api_error(
            400,
            "NOT_ENOUGH_GARMENTS",
            "Aún no tengo suficientes prendas. Agrega al menos una de arriba, "
            "una de abajo y un calzado.",
        )
    return {
        "outfits": [
            {
                "garment_ids": fallback.garment_ids,
                "explanation": fallback.explanation,
                "projected_image": fallback.projected_image,
            }
        ],
        "source": "reglas",
    }
