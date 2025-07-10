"""
Add LLM analysis fields

Revision ID: add_llm_analysis_fields
Revises: 20250706015740
Create Date: 2025-07-07 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'add_llm_analysis_fields'
down_revision: Union[str, None] = '20250706015740'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add LLM analysis fields to backtest_trades table
    op.add_column('backtest_trades', sa.Column('llm_reasoning', sa.Text))
    op.add_column('backtest_trades', sa.Column('llm_analysis', postgresql.JSONB))
    op.add_column('backtest_trades', sa.Column('llm_sanity_check', postgresql.JSONB))
    op.add_column('backtest_trades', sa.Column('llm_approved', sa.String(10)))
    op.add_column('backtest_trades', sa.Column('llm_risk_level', sa.String(20)))
    op.add_column('backtest_trades', sa.Column('llm_warnings', postgresql.JSONB))
    op.add_column('backtest_trades', sa.Column('llm_recommendations', postgresql.JSONB))


def downgrade() -> None:
    # Remove LLM analysis fields from backtest_trades table
    op.drop_column('backtest_trades', 'llm_reasoning')
    op.drop_column('backtest_trades', 'llm_analysis')
    op.drop_column('backtest_trades', 'llm_sanity_check')
    op.drop_column('backtest_trades', 'llm_approved')
    op.drop_column('backtest_trades', 'llm_risk_level')
    op.drop_column('backtest_trades', 'llm_warnings')
    op.drop_column('backtest_trades', 'llm_recommendations') 