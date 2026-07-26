"""Outfit guardado (favorito) y perfil de estilo del usuario.

Un Outfit es un conjunto que la IA armó y el usuario marcó con ⭐. Guardamos qué prendas
lo formaban, para qué ocasión, qué quería proyectar y la explicación del asesor — así el
favorito se ve completo aunque pasen meses, y la IA aprende qué le gusta al usuario.
"""

from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SyncMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Outfit(UUIDPrimaryKeyMixin, SyncMixin, Base):
    __tablename__ = "outfits"

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # IDs de las prendas usadas, separados por coma (el orden es el del outfit).
    garment_ids: Mapped[str] = mapped_column(Text, default="", server_default="")
    occasion: Mapped[str] = mapped_column(String(40), default="", server_default="")
    projection: Mapped[str] = mapped_column(String(40), default="", server_default="")
    # La frase del asesor: por qué funciona y qué imagen proyecta.
    explanation: Mapped[str] = mapped_column(Text, default="", server_default="")


class StyleProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Preferencias del usuario. Opcionales: la IA deduce el estilo de la propia ropa."""

    __tablename__ = "style_profiles"

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    # Estilos preferidos, CSV: "moderno,casual".
    styles: Mapped[str] = mapped_column(String(200), default="", server_default="")
    # Colores que NO le gustan, CSV: "amarillo,rosa".
    avoid_colors: Mapped[str] = mapped_column(String(200), default="", server_default="")
