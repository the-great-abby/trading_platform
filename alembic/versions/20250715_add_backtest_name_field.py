"""
Add backtest_name field to track which backtest file was used

Revision ID: 20250715_add_backtest_name_field
Revises: 20250715_add_historical_options_snapshots
Create Date: 2025-07-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250715_add_backtest_name_field'
down_revision: Union[str, None] = '20250715_add_historical_options_snapshots'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add backtest_name field to backtest_runs table
    op.add_column('backtest_runs', sa.Column('backtest_name', sa.String(200), nullable=True))
    
    # Create index for efficient querying by backtest name
    op.create_index('idx_backtest_name', 'backtest_runs', ['backtest_name'])


def downgrade() -> None:
    # Remove index
    op.drop_index('idx_backtest_name', table_name='backtest_runs')
    
    # Remove column
    op.drop_column('backtest_runs', 'backtest_name') 