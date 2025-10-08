"""
Database migration: Create strategy management tables

Creates tables for strategy configurations, risk management, and trailing stops.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


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
    
    # Add new columns to risk_profiles table
    op.add_column('risk_profiles', sa.Column('risk_level', sa.String(length=20), nullable=True))
    op.add_column('risk_profiles', sa.Column('position_limits', sa.Text(), nullable=True))  # JSON object
    op.add_column('risk_profiles', sa.Column('emergency_controls', sa.Text(), nullable=True))  # JSON object


def downgrade():
    """Drop strategy management tables."""
    
    # Remove columns from risk_profiles table
    op.drop_column('risk_profiles', 'emergency_controls')
    op.drop_column('risk_profiles', 'position_limits')
    op.drop_column('risk_profiles', 'risk_level')
    
    # Drop tables
    op.drop_table('trailing_stop_configurations')
    op.drop_table('strategy_configurations')























