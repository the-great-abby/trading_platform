"""add strategy management tables

Revision ID: 20250927_strategy_tables
Revises: 20250723_add_missing_tables
Create Date: 2025-09-27 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250927_strategy_tables'
down_revision = '20250723_add_missing_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Create strategy management tables."""
    
    # Create strategy_configurations table
    op.create_table(
        'strategy_configurations',
        sa.Column('strategy_id', sa.String(length=100), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('strategy_name', sa.String(length=50), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('max_position_size', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('max_risk_per_trade', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('max_daily_trades', sa.Integer(), nullable=False),
        sa.Column('max_daily_loss', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('symbols', sa.Text(), nullable=False),  # JSON array
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('strategy_id'),
        sa.ForeignKeyConstraint(['account_id'], ['live_trading_accounts.account_id'], ondelete='CASCADE')
    )
    
    # Create trailing_stop_configurations table
    op.create_table(
        'trailing_stop_configurations',
        sa.Column('trailing_stop_id', sa.String(length=100), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('strategy_name', sa.String(length=50), nullable=False),
        sa.Column('profit_threshold', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('trail_percentage', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('min_profit', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('trailing_stop_id'),
        sa.ForeignKeyConstraint(['account_id'], ['live_trading_accounts.account_id'], ondelete='CASCADE')
    )
    
    # Add new columns to risk_profiles table if they don't exist
    try:
        op.add_column('risk_profiles', sa.Column('risk_level', sa.String(length=20), nullable=True))
    except Exception:
        pass  # Column may already exist
    
    try:
        op.add_column('risk_profiles', sa.Column('position_limits', sa.Text(), nullable=True))  # JSON object
    except Exception:
        pass  # Column may already exist
    
    try:
        op.add_column('risk_profiles', sa.Column('emergency_controls', sa.Text(), nullable=True))  # JSON object
    except Exception:
        pass  # Column may already exist


def downgrade():
    """Drop strategy management tables."""
    
    # Remove columns from risk_profiles table
    try:
        op.drop_column('risk_profiles', 'emergency_controls')
    except Exception:
        pass
    
    try:
        op.drop_column('risk_profiles', 'position_limits')
    except Exception:
        pass
    
    try:
        op.drop_column('risk_profiles', 'risk_level')
    except Exception:
        pass
    
    # Drop tables
    op.drop_table('trailing_stop_configurations')
    op.drop_table('strategy_configurations')











