"""
Database migration: Create live trading tables

Creates all tables for the live trading system.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    """Create live trading tables."""
    
    # Create enum types
    op.execute("CREATE TYPE accounttype AS ENUM ('CASH', 'MARGIN')")
    op.execute("CREATE TYPE tradestatus AS ENUM ('PENDING', 'SUBMITTED', 'FILLED', 'PARTIALLY_FILLED', 'CANCELLED', 'REJECTED', 'EXPIRED')")
    op.execute("CREATE TYPE positionstatus AS ENUM ('OPEN', 'CLOSED', 'EXPIRED')")
    op.execute("CREATE TYPE strategytype AS ENUM ('IRON_CONDOR', 'BUTTERFLY_SPREAD', 'CALENDAR_SPREAD')")
    op.execute("CREATE TYPE optiontype AS ENUM ('CALL', 'PUT')")
    op.execute("CREATE TYPE tradeaction AS ENUM ('BUY', 'SELL')")
    op.execute("CREATE TYPE risklevel AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')")
    
    # Create live_trading_accounts table
    op.create_table(
        'live_trading_accounts',
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('public_account_id', sa.String(length=100), nullable=False),
        sa.Column('account_name', sa.String(length=255), nullable=False),
        sa.Column('account_type', sa.Enum('CASH', 'MARGIN', name='accounttype'), nullable=False),
        sa.Column('buying_power', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('cash_balance', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('equity', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('account_id'),
        sa.UniqueConstraint('public_account_id')
    )
    
    # Create live_positions table
    op.create_table(
        'live_positions',
        sa.Column('position_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('strategy', sa.Enum('IRON_CONDOR', 'BUTTERFLY_SPREAD', 'CALENDAR_SPREAD', name='strategytype'), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('average_price', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('current_price', sa.Numeric(precision=10, scale=4)),
        sa.Column('unrealized_pnl', sa.Numeric(precision=15, scale=2), server_default='0.00'),
        sa.Column('realized_pnl', sa.Numeric(precision=15, scale=2), server_default='0.00'),
        sa.Column('status', sa.Enum('OPEN', 'CLOSED', 'EXPIRED', name='positionstatus'), nullable=False, server_default='OPEN'),
        sa.Column('opened_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('closed_at', sa.DateTime()),
        sa.Column('expiration_date', sa.DateTime()),
        sa.Column('legs_data', sa.Text()),
        sa.Column('greeks_data', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['account_id'], ['live_trading_accounts.account_id'], ),
        sa.PrimaryKeyConstraint('position_id')
    )
    
    # Create live_trades table
    op.create_table(
        'live_trades',
        sa.Column('trade_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('position_id', postgresql.UUID(as_uuid=True)),
        sa.Column('public_order_id', sa.String(length=100), nullable=False),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('action', sa.Enum('BUY', 'SELL', name='tradeaction'), nullable=False),
        sa.Column('option_type', sa.Enum('CALL', 'PUT', name='optiontype')),
        sa.Column('strike_price', sa.Numeric(precision=10, scale=4)),
        sa.Column('expiration_date', sa.DateTime()),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('price', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('commission', sa.Numeric(precision=10, scale=4), server_default='0.00'),
        sa.Column('status', sa.Enum('PENDING', 'SUBMITTED', 'FILLED', 'PARTIALLY_FILLED', 'CANCELLED', 'REJECTED', 'EXPIRED', name='tradestatus'), nullable=False, server_default='PENDING'),
        sa.Column('filled_quantity', sa.Integer(), server_default='0'),
        sa.Column('remaining_quantity', sa.Integer(), nullable=False),
        sa.Column('filled_at', sa.DateTime()),
        sa.Column('cancelled_at', sa.DateTime()),
        sa.Column('rejection_reason', sa.Text()),
        sa.Column('strategy', sa.Enum('IRON_CONDOR', 'BUTTERFLY_SPREAD', 'CALENDAR_SPREAD', name='strategytype')),
        sa.Column('leg_data', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['account_id'], ['live_trading_accounts.account_id'], ),
        sa.ForeignKeyConstraint(['position_id'], ['live_positions.position_id'], ),
        sa.PrimaryKeyConstraint('trade_id'),
        sa.UniqueConstraint('public_order_id')
    )
    
    # Create risk_profiles table
    op.create_table(
        'risk_profiles',
        sa.Column('risk_profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('max_position_size', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('max_portfolio_risk', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('max_daily_loss', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('max_daily_trades', sa.Integer(), nullable=False),
        sa.Column('allowed_strategies', sa.Text(), nullable=False),
        sa.Column('max_greeks_exposure', sa.Text(), nullable=False),
        sa.Column('emergency_stop_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('emergency_stop_reason', sa.Text()),
        sa.Column('emergency_stop_activated_at', sa.DateTime()),
        sa.Column('risk_level', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='risklevel'), nullable=False, server_default='MEDIUM'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['account_id'], ['live_trading_accounts.account_id'], ),
        sa.PrimaryKeyConstraint('risk_profile_id'),
        sa.UniqueConstraint('account_id')
    )
    
    # Create api_credentials table
    op.create_table(
        'api_credentials',
        sa.Column('credential_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('encrypted_api_key', sa.Text(), nullable=False),
        sa.Column('encrypted_api_secret', sa.Text(), nullable=False),
        sa.Column('access_token', sa.Text()),
        sa.Column('refresh_token', sa.Text()),
        sa.Column('token_expires_at', sa.DateTime()),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_used_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['account_id'], ['live_trading_accounts.account_id'], ),
        sa.PrimaryKeyConstraint('credential_id')
    )
    
    # Create trade_signals table
    op.create_table(
        'trade_signals',
        sa.Column('signal_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('strategy', sa.Enum('IRON_CONDOR', 'BUTTERFLY_SPREAD', 'CALENDAR_SPREAD', name='strategytype'), nullable=False),
        sa.Column('signal_type', sa.String(length=50), nullable=False),
        sa.Column('signal_strength', sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column('confidence_score', sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column('market_conditions', sa.Text()),
        sa.Column('signal_data', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('executed_at', sa.DateTime()),
        sa.Column('executed_trade_id', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime()),
        sa.ForeignKeyConstraint(['account_id'], ['live_trading_accounts.account_id'], ),
        sa.ForeignKeyConstraint(['executed_trade_id'], ['live_trades.trade_id'], ),
        sa.PrimaryKeyConstraint('signal_id')
    )
    
    # Create order_status_history table
    op.create_table(
        'order_status_history',
        sa.Column('status_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trade_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_id', sa.String(length=100), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'SUBMITTED', 'FILLED', 'PARTIALLY_FILLED', 'CANCELLED', 'REJECTED', 'EXPIRED', name='tradestatus'), nullable=False),
        sa.Column('status_message', sa.Text()),
        sa.Column('filled_quantity', sa.Integer(), server_default='0'),
        sa.Column('remaining_quantity', sa.Integer(), nullable=False),
        sa.Column('average_price', sa.Numeric(precision=10, scale=4)),
        sa.Column('commission', sa.Numeric(precision=10, scale=4), server_default='0.00'),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('external_status', sa.Text()),
        sa.Column('error_details', sa.Text()),
        sa.ForeignKeyConstraint(['trade_id'], ['live_trades.trade_id'], ),
        sa.PrimaryKeyConstraint('status_id')
    )


def downgrade():
    """Drop live trading tables."""
    
    # Drop tables in reverse order
    op.drop_table('order_status_history')
    op.drop_table('trade_signals')
    op.drop_table('api_credentials')
    op.drop_table('risk_profiles')
    op.drop_table('live_trades')
    op.drop_table('live_positions')
    op.drop_table('live_trading_accounts')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS risklevel")
    op.execute("DROP TYPE IF EXISTS tradeaction")
    op.execute("DROP TYPE IF EXISTS optiontype")
    op.execute("DROP TYPE IF EXISTS strategytype")
    op.execute("DROP TYPE IF EXISTS positionstatus")
    op.execute("DROP TYPE IF EXISTS tradestatus")
    op.execute("DROP TYPE IF EXISTS accounttype")
