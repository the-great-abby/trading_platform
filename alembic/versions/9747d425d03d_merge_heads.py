"""merge heads

Revision ID: 9747d425d03d
Revises: 20250715_add_backtest_name_field, 20250717_add_greeks_data_tables, 54cf8470e4a2
Create Date: 2025-07-17 13:46:54.070438

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9747d425d03d'
down_revision: Union[str, None] = ('20250715_add_backtest_name_field', '20250717_add_greeks_data_tables', '54cf8470e4a2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
