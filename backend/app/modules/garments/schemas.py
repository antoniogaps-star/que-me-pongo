"""Contratos del módulo de prendas."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

Category = Literal["arriba", "abajo", "abrigo", "calzado", "accesorio", "completo"]
Season = Literal["todo", "calor", "frio"]
# Los 10 estilos del PRD. Una prenda puede tener varios.
Style = Literal[
    "casual",
    "moderno",
    "clasico",
    "rockero",
    "deportivo",
    "elegante",
    "streetwear",
    "ranchero",
    "ejecutivo",
    "minimalista",
]


class GarmentCreate(BaseModel):
    category: Category
    name: Annotated[str, Field(min_length=1, max_length=120)]
    color: str | None = None
    styles: list[Style] = []
    # 1 = muy informal, 10 = etiqueta. 5 es un punto medio seguro.
    formality: Annotated[int, Field(ge=1, le=10)] = 5
    season: Season = "todo"


class GarmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category: str
    name: str
    color: str | None
    styles: list[str]
    formality: int
    season: str
