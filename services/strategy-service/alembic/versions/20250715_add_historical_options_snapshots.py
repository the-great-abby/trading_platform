"""
Add historical options snapshots table for backtesting

Revision ID: 20250715_add_historical_options_snapshots
Revises: merge_final_heads
Create Date: 2025-07-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250715_add_historical_options_snapshots'
down_revision: Union[str, None] = 'merge_final_heads_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create historical options snapshots table
    op.create_table(
        'historical_options_snapshots',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('symbol', sa.String, index=True),
        sa.Column('snapshot_date', sa.Date, index=True),  # Date when snapshot was taken
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
        sa.Column('underlying_price', sa.Float),  # Stock price when snapshot was taken
        sa.Column('data_source', sa.String),  # Source of the data (polygon, etc.)
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create composite indexes for efficient historical queries
    op.create_index('idx_historical_options_symbol_date', 'historical_options_snapshots', ['symbol', 'snapshot_date'])
    op.create_index('idx_historical_options_symbol_expiration', 'historical_options_snapshots', ['symbol', 'expiration'])
    op.create_index('idx_historical_options_date_range', 'historical_options_snapshots', ['snapshot_date'])
    op.create_index('idx_historical_options_symbol_date_expiration', 'historical_options_snapshots', ['symbol', 'snapshot_date', 'expiration'])


def downgrade() -> None:
    op.drop_table('historical_options_snapshots') 