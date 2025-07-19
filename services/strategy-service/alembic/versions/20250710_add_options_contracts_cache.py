"""
Add options_contracts_cache table for options data caching

Revision ID: 20250710_add_options_contracts_cache
Revises: ca647495b800
Create Date: 2025-07-10 07:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250710_add_options_contracts_cache'
down_revision: Union[str, None] = 'ca647495b800'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'options_contracts_cache',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('symbol', sa.String, index=True),
        sa.Column('expiration', sa.String, index=True),
        sa.Column('strike', sa.Float),
        sa.Column('option_type', sa.String),
        sa.Column('price', sa.Float),
        sa.Column('volume', sa.Integer),
        sa.Column('open_interest', sa.Integer),
        sa.Column('delta', sa.Float),
        sa.Column('gamma', sa.Float),
        sa.Column('theta', sa.Float),
        sa.Column('vega', sa.Float),
        sa.Column('implied_volatility', sa.Float),
        sa.Column('cache_date', sa.Date, index=True),
        sa.Column('last_updated', sa.DateTime)
    )


def downgrade() -> None:
    op.drop_table('options_contracts_cache') 