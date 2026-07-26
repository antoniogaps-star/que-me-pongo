"""Modelo Garment (prenda del clóset: ropa o zapatos). Tenant, sincronizable (LWW).

La FOTO no vive aquí: en la v1 se guarda local en el celular. El backend solo respalda la
ficha (categoría, color, estilos) para que la recomendación funcione y esté respaldada.
"""

from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SyncMixin, UUIDPrimaryKeyMixin

# Dónde va la prenda en el outfit.
CATEGORIES = ("arriba", "abajo", "abrigo", "calzado", "completo")


class Garment(UUIDPrimaryKeyMixin, SyncMixin, Base):
    __tablename__ = "garments"
    __table_args__ = (
        CheckConstraint(f"category IN {CATEGORIES}", name="ck_garments_category"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False
    )
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    color: Mapped[str | None] = mapped_column(String(40), nullable=True)
    # Estilos que le quedan, separados por coma: "casual,rockero,ejecutivo".
    styles: Mapped[str] = mapped_column(String(200), default="", server_default="")
