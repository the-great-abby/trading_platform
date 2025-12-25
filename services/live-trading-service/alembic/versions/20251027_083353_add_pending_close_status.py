"""add pending_close status

Revision ID: add_pending_close
Revises: 
Create Date: 2025-10-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_pending_close'
down_revision = None  # Update this if you know the previous revision
branch_labels = None
depends_on = None


def upgrade():
    # Add PENDING_CLOSE to positionstatus enum
    op.execute("ALTER TYPE positionstatus ADD VALUE IF NOT EXISTS 'PENDING_CLOSE'")


def downgrade():
    # Cannot easily remove enum values in PostgreSQL
    pass
