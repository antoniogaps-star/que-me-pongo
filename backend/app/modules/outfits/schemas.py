"""Contratos de favoritos y perfil de estilo."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.garments.schemas import Style

# Para qué es el outfit.
Occasion = str
# Qué imagen quiere dar el usuario.
Projection = str


class OutfitCreate(BaseModel):
    garment_ids: list[UUID]
    occasion: str = ""
    projection: str = ""
    explanation: str = ""


class OutfitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    garment_ids: list[UUID]
    occasion: str
    projection: str
    explanation: str


class StyleProfileUpdate(BaseModel):
    styles: list[Style] = []
    avoid_colors: list[str] = []


class StyleProfileRead(BaseModel):
    styles: list[str]
    avoid_colors: list[str]
