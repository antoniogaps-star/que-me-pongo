"""Respaldo de las fotos del clóset.

Hasta ahora la foto vivía **solo** en el celular: al cambiar de teléfono o reinstalar la
app, el clóset se recuperaba sin imágenes. Aquí se guarda una copia para que sobreviva y
para que el panel web pueda mostrarla.

Se guarda en una tabla aparte, no como columna de `garments`, por una razón concreta: la
sincronización lee la ficha de cada prenda muchas veces al día, y arrastrar los bytes de
la imagen en cada lectura la volvería lenta y cara. Aquí la imagen solo se toca cuando
alguien la pide.

Los bytes van en Postgres y no en un servicio de archivos aparte para no depender de otra
cuenta ni de otras credenciales. A la escala de esta app —un clóset personal, fotos ya
comprimidas por el celular— cabe de sobra; si algún día crece, se cambia esta tabla por
almacenamiento de objetos sin tocar el resto.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, String, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.modules.garments.models import Garment
from app.shared.errors import api_error

# Tope por foto. El celular ya la manda comprimida (~200 KB); 3 MB es margen de sobra y
# a la vez impide que alguien suba un archivo enorme y llene la base.
MAX_BYTES = 3 * 1024 * 1024

TIPOS_PERMITIDOS = ("image/jpeg", "image/png", "image/webp")


class GarmentPhoto(Base):
    __tablename__ = "garment_photos"

    # La prenda es la llave: una foto por prenda, y si la prenda se borra de verdad, la
    # foto se va con ella.
    garment_id: Mapped[UUID] = mapped_column(
        ForeignKey("garments.id", ondelete="CASCADE"), primary_key=True
    )
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False
    )
    content_type: Mapped[str] = mapped_column(String(40), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


async def _prenda_propia(session: AsyncSession, garment_id: UUID, tenant_id: UUID) -> None:
    """La prenda tiene que ser de ESTE clóset.

    Sin esta comprobación cualquiera podría subir o leer la foto de la ropa de otra
    persona sabiendo un id.
    """
    rows = await session.execute(
        select(Garment.id).where(
            Garment.id == garment_id,
            Garment.tenant_id == tenant_id,
            Garment.is_deleted.is_(False),
        )
    )
    if rows.first() is None:
        raise api_error(404, "GARMENT_NOT_FOUND", "Prenda no encontrada")


async def guardar(
    session: AsyncSession,
    *,
    garment_id: UUID,
    tenant_id: UUID,
    data: bytes,
    content_type: str,
) -> GarmentPhoto:
    await _prenda_propia(session, garment_id, tenant_id)

    if content_type not in TIPOS_PERMITIDOS:
        raise api_error(415, "UNSUPPORTED_IMAGE", "Solo se aceptan JPG, PNG o WebP")
    if len(data) > MAX_BYTES:
        raise api_error(413, "IMAGE_TOO_LARGE", "La imagen pesa demasiado")
    if not data:
        raise api_error(422, "EMPTY_IMAGE", "La imagen llegó vacía")

    actual = await obtener(session, garment_id, tenant_id)
    if actual is None:
        actual = GarmentPhoto(
            garment_id=garment_id,
            tenant_id=tenant_id,
            content_type=content_type,
            size_bytes=len(data),
            data=data,
        )
        session.add(actual)
    else:
        actual.content_type = content_type
        actual.size_bytes = len(data)
        actual.data = data
        actual.updated_at = datetime.now(UTC)

    await session.flush()
    return actual


async def obtener(
    session: AsyncSession, garment_id: UUID, tenant_id: UUID
) -> GarmentPhoto | None:
    """Busca la foto SOLO dentro de este clóset."""
    rows = await session.execute(
        select(GarmentPhoto).where(
            GarmentPhoto.garment_id == garment_id,
            GarmentPhoto.tenant_id == tenant_id,
        )
    )
    return rows.scalars().first()


async def borrar(session: AsyncSession, garment_id: UUID, tenant_id: UUID) -> None:
    foto = await obtener(session, garment_id, tenant_id)
    if foto is not None:
        await session.delete(foto)
        await session.flush()


async def con_foto(session: AsyncSession, tenant_id: UUID) -> set[UUID]:
    """Qué prendas de este clóset ya tienen foto respaldada.

    El móvil lo usa para saber qué le falta subir y qué puede bajar, sin pedir las
    imágenes una por una.
    """
    rows = await session.execute(
        select(GarmentPhoto.garment_id).where(GarmentPhoto.tenant_id == tenant_id)
    )
    return {fila[0] for fila in rows.all()}
