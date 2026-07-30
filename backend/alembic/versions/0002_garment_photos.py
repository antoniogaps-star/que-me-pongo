"""Respaldo de las fotos del clóset.

Hasta ahora la foto vivía solo en el celular: al cambiar de teléfono se perdía. Va en
tabla aparte y no como columna de `garments` porque la sincronización lee la ficha de
cada prenda muchas veces al día, y arrastrar los bytes de la imagen la volvería lenta.

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "garment_photos",
        sa.Column("garment_id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("content_type", sa.String(length=40), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["garment_id"], ["garments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("garment_id"),
    )
    op.create_index("ix_garment_photos_tenant_id", "garment_photos", ["tenant_id"])

    # Mismo candado que el resto de las tablas: cada clóset ve solo lo suyo.
    op.execute("ALTER TABLE garment_photos ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE garment_photos FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON garment_photos
        USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
        WITH CHECK (tenant_id = current_setting('app.current_tenant', true)::uuid)
        """
    )


def downgrade() -> None:
    op.drop_index("ix_garment_photos_tenant_id", table_name="garment_photos")
    op.drop_table("garment_photos")
