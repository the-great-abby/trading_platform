"""add_rejected_trade_attempts

Revision ID: 20251015_163213
Revises: 
Create Date: 2025-10-15 16:32:13.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '20251015_163213'
down_revision: Union[str, None] = '20250723_add_missing_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add rejected_trade_attempts table"""
    op.create_table(
        'rejected_trade_attempts',
        sa.Column('attempt_id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('account_id', UUID(as_uuid=True), sa.ForeignKey('live_trading_accounts.account_id'), nullable=False),
        sa.Column('symbol', sa.String(50), nullable=False),
        sa.Column('strategy', sa.String(100), nullable=False),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('quantity', sa.Integer, nullable=True),
        sa.Column('estimated_premium', sa.Numeric(15, 2), nullable=True),
        sa.Column('rejection_reason', sa.Text, nullable=False),
        sa.Column('rejection_category', sa.String(50), nullable=False),
        sa.Column('confidence_score', sa.Numeric(5, 4), nullable=True),
        sa.Column('current_price', sa.Numeric(10, 4), nullable=True),
        sa.Column('option_type', sa.String(10), nullable=True),
        sa.Column('strike_price', sa.Numeric(10, 4), nullable=True),
        sa.Column('expiration_date', sa.DateTime, nullable=True),
        sa.Column('rejection_details', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    
    # Create indexes for common queries
    op.create_index('ix_rejected_attempts_account_id', 'rejected_trade_attempts', ['account_id'])
    op.create_index('ix_rejected_attempts_symbol', 'rejected_trade_attempts', ['symbol'])
    op.create_index('ix_rejected_attempts_created_at', 'rejected_trade_attempts', ['created_at'])
    op.create_index('ix_rejected_attempts_category', 'rejected_trade_attempts', ['rejection_category'])


def downgrade() -> None:
    """Drop rejected_trade_attempts table"""
    op.drop_index('ix_rejected_attempts_category', table_name='rejected_trade_attempts')
    op.drop_index('ix_rejected_attempts_created_at', table_name='rejected_trade_attempts')
    op.drop_index('ix_rejected_attempts_symbol', table_name='rejected_trade_attempts')
    op.drop_index('ix_rejected_attempts_account_id', table_name='rejected_trade_attempts')
    op.drop_table('rejected_trade_attempts')

