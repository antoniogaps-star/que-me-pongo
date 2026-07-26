"""Contratos del asesor de imagen."""

from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.garments.schemas import Category, Season, Style


class ClassifyRequest(BaseModel):
    """Foto de UNA prenda, en base64 (el móvil la manda al tomarla)."""

    image_base64: Annotated[str, Field(min_length=1)]
    media_type: str = "image/jpeg"


class ClassifyResponse(BaseModel):
    category: Category
    name: str
    color: str
    styles: list[Style]
    formality: Annotated[int, Field(ge=1, le=10)]
    season: Season


class RecommendRequest(BaseModel):
    occasion: str = "dia normal"
    projection: str = ""
    temperature_c: float | None = None
    # "¿Con qué combino esto?": obliga a incluir esta prenda.
    with_garment_id: UUID | None = None
    # "Sorpréndeme": busca combinaciones distintas a las que ya usa.
    surprise: bool = False
    count: Annotated[int, Field(ge=1, le=3)] = 1


class OutfitSuggestion(BaseModel):
    garment_ids: list[UUID]
    explanation: str
    projected_image: str


class RecommendResponse(BaseModel):
    outfits: list[OutfitSuggestion]
    # "claude" o "reglas": para que el móvil pueda avisar cuando va en modo sin conexión.
    source: str
