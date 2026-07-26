"""Modelo Garment (prenda del clóset: ropa, calzado o accesorio). Tenant, sync (LWW).

La FOTO no vive aquí: en la v1 se guarda local en el celular. El backend solo respalda la
ficha (categoría, color, estilos, formalidad) para que la recomendación funcione.

`formality` (1–10) es el dato que evita el ridículo: sin él la IA te pone tenis en una boda.
1 = pants de dormir · 5 = jeans y playera · 8 = camisa y saco · 10 = traje formal.
"""

from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SyncMixin, UUIDPrimaryKeyMixin

# Dónde va la prenda en el outfit.
CATEGORIES = ("arriba", "abajo", "abrigo", "calzado", "accesorio", "completo")
# Para qué clima sirve.
SEASONS = ("todo", "calor", "frio")


class Garment(UUIDPrimaryKeyMixin, SyncMixin, Base):
    __tablename__ = "garments"
    __table_args__ = (
        CheckConstraint(f"category IN {CATEGORIES}", name="ck_garments_category"),
        CheckConstraint(f"season IN {SEASONS}", name="ck_garments_season"),
        CheckConstraint(
            "formality BETWEEN 1 AND 10", name="ck_garments_formality_range"
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False
    )
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    color: Mapped[str | None] = mapped_column(String(40), nullable=True)
    # Estilos que le quedan, separados por coma: "casual,rockero,ejecutivo".
    styles: Mapped[str] = mapped_column(String(200), default="", server_default="")
    # Qué tan formal es (1–10). 5 = neutro, sirve para casi todo.
    formality: Mapped[int] = mapped_column(
        Integer, default=5, server_default="5", nullable=False
    )
    season: Mapped[str] = mapped_column(
        String(10), default="todo", server_default="todo", nullable=False
    )
