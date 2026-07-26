"""Contratos del módulo de prendas."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

Category = Literal["arriba", "abajo", "abrigo", "calzado", "completo"]
Style = Literal["casual", "formal", "rockero", "rapero", "ejecutivo"]


class GarmentCreate(BaseModel):
    category: Category
    name: Annotated[str, Field(min_length=1, max_length=120)]
    color: str | None = None
    styles: list[Style] = []


class GarmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category: str
    name: str
    color: str | None
    styles: list[str]
