"""merge heads

Revision ID: 54cf8470e4a2
Revises: 20250711_partition_tables_by_symbol, merge_final_heads_001
Create Date: 2025-07-11 14:39:13.865998

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '54cf8470e4a2'
down_revision: Union[str, None] = ('20250711_partition_tables_by_symbol', 'merge_final_heads_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
