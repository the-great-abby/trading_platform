"""
Database migration: Create indexes and constraints

Creates indexes and constraints for the live trading tables.
"""

from alembic import op
import sqlalchemy as sa


def upgrade():
    """Create indexes and constraints."""
    
    # Indexes for live_trading_accounts
    op.create_index('idx_live_accounts_public_id', 'live_trading_accounts', ['public_account_id'])
    op.create_index('idx_live_accounts_active', 'live_trading_accounts', ['is_active'])
    op.create_index('idx_live_accounts_created_at', 'live_trading_accounts', ['created_at'])
    
    # Indexes for live_positions
    op.create_index('idx_live_positions_account_id', 'live_positions', ['account_id'])
    op.create_index('idx_live_positions_symbol', 'live_positions', ['symbol'])
    op.create_index('idx_live_positions_strategy', 'live_positions', ['strategy'])
    op.create_index('idx_live_positions_status', 'live_positions', ['status'])
    op.create_index('idx_live_positions_expiration', 'live_positions', ['expiration_date'])
    op.create_index('idx_live_positions_opened_at', 'live_positions', ['opened_at'])
    
    # Indexes for live_trades
    op.create_index('idx_live_trades_account_id', 'live_trades', ['account_id'])
    op.create_index('idx_live_trades_position_id', 'live_trades', ['position_id'])
    op.create_index('idx_live_trades_public_order_id', 'live_trades', ['public_order_id'])
    op.create_index('idx_live_trades_symbol', 'live_trades', ['symbol'])
    op.create_index('idx_live_trades_status', 'live_trades', ['status'])
    op.create_index('idx_live_trades_strategy', 'live_trades', ['strategy'])
    op.create_index('idx_live_trades_created_at', 'live_trades', ['created_at'])
    op.create_index('idx_live_trades_filled_at', 'live_trades', ['filled_at'])
    
    # Indexes for risk_profiles
    op.create_index('idx_risk_profiles_account_id', 'risk_profiles', ['account_id'])
    op.create_index('idx_risk_profiles_emergency_stop', 'risk_profiles', ['emergency_stop_active'])
    op.create_index('idx_risk_profiles_risk_level', 'risk_profiles', ['risk_level'])
    
    # Indexes for api_credentials
    op.create_index('idx_api_credentials_account_id', 'api_credentials', ['account_id'])
    op.create_index('idx_api_credentials_active', 'api_credentials', ['is_active'])
    op.create_index('idx_api_credentials_last_used', 'api_credentials', ['last_used_at'])
    
    # Indexes for trade_signals
    op.create_index('idx_trade_signals_account_id', 'trade_signals', ['account_id'])
    op.create_index('idx_trade_signals_symbol', 'trade_signals', ['symbol'])
    op.create_index('idx_trade_signals_strategy', 'trade_signals', ['strategy'])
    op.create_index('idx_trade_signals_status', 'trade_signals', ['status'])
    op.create_index('idx_trade_signals_created_at', 'trade_signals', ['created_at'])
    op.create_index('idx_trade_signals_expires_at', 'trade_signals', ['expires_at'])
    
    # Indexes for order_status_history
    op.create_index('idx_order_status_trade_id', 'order_status_history', ['trade_id'])
    op.create_index('idx_order_status_order_id', 'order_status_history', ['order_id'])
    op.create_index('idx_order_status_status', 'order_status_history', ['status'])
    op.create_index('idx_order_status_timestamp', 'order_status_history', ['timestamp'])
    
    # Composite indexes for common queries
    op.create_index('idx_positions_account_status', 'live_positions', ['account_id', 'status'])
    op.create_index('idx_trades_account_status', 'live_trades', ['account_id', 'status'])
    op.create_index('idx_trades_symbol_status', 'live_trades', ['symbol', 'status'])
    op.create_index('idx_signals_account_strategy', 'trade_signals', ['account_id', 'strategy'])
    op.create_index('idx_signals_symbol_status', 'trade_signals', ['symbol', 'status'])
    
    # Add check constraints
    op.create_check_constraint(
        'chk_buying_power_positive',
        'live_trading_accounts',
        'buying_power >= 0'
    )
    
    op.create_check_constraint(
        'chk_cash_balance_positive',
        'live_trading_accounts',
        'cash_balance >= 0'
    )
    
    op.create_check_constraint(
        'chk_equity_positive',
        'live_trading_accounts',
        'equity >= 0'
    )
    
    op.create_check_constraint(
        'chk_position_quantity_nonzero',
        'live_positions',
        'quantity != 0'
    )
    
    op.create_check_constraint(
        'chk_trade_quantity_positive',
        'live_trades',
        'quantity > 0'
    )
    
    op.create_check_constraint(
        'chk_trade_price_positive',
        'live_trades',
        'price > 0'
    )
    
    op.create_check_constraint(
        'chk_risk_max_position_positive',
        'risk_profiles',
        'max_position_size > 0'
    )
    
    op.create_check_constraint(
        'chk_risk_max_portfolio_risk_valid',
        'risk_profiles',
        'max_portfolio_risk > 0 AND max_portfolio_risk <= 1'
    )
    
    op.create_check_constraint(
        'chk_risk_max_daily_loss_positive',
        'risk_profiles',
        'max_daily_loss > 0'
    )
    
    op.create_check_constraint(
        'chk_risk_max_daily_trades_positive',
        'risk_profiles',
        'max_daily_trades > 0'
    )
    
    op.create_check_constraint(
        'chk_signal_strength_valid',
        'trade_signals',
        'signal_strength >= 0 AND signal_strength <= 1'
    )
    
    op.create_check_constraint(
        'chk_confidence_score_valid',
        'trade_signals',
        'confidence_score >= 0 AND confidence_score <= 1'
    )
    
    # Add triggers for updated_at timestamps
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Create triggers for updated_at columns
    tables_with_updated_at = [
        'live_trading_accounts',
        'live_positions', 
        'live_trades',
        'risk_profiles',
        'api_credentials'
    ]
    
    for table in tables_with_updated_at:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at 
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade():
    """Drop indexes and constraints."""
    
    # Drop triggers
    tables_with_updated_at = [
        'live_trading_accounts',
        'live_positions',
        'live_trades', 
        'risk_profiles',
        'api_credentials'
    ]
    
    for table in tables_with_updated_at:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table};")
    
    # Drop function
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
    
    # Drop check constraints
    check_constraints = [
        'chk_buying_power_positive',
        'chk_cash_balance_positive', 
        'chk_equity_positive',
        'chk_position_quantity_nonzero',
        'chk_trade_quantity_positive',
        'chk_trade_price_positive',
        'chk_risk_max_position_positive',
        'chk_risk_max_portfolio_risk_valid',
        'chk_risk_max_daily_loss_positive',
        'chk_risk_max_daily_trades_positive',
        'chk_signal_strength_valid',
        'chk_confidence_score_valid'
    ]
    
    for constraint in check_constraints:
        op.drop_constraint(constraint, 'live_trading_accounts', type_='check')
    
    # Drop indexes
    indexes = [
        # Single column indexes
        'idx_live_accounts_public_id', 'idx_live_accounts_active', 'idx_live_accounts_created_at',
        'idx_live_positions_account_id', 'idx_live_positions_symbol', 'idx_live_positions_strategy',
        'idx_live_positions_status', 'idx_live_positions_expiration', 'idx_live_positions_opened_at',
        'idx_live_trades_account_id', 'idx_live_trades_position_id', 'idx_live_trades_public_order_id',
        'idx_live_trades_symbol', 'idx_live_trades_status', 'idx_live_trades_strategy',
        'idx_live_trades_created_at', 'idx_live_trades_filled_at',
        'idx_risk_profiles_account_id', 'idx_risk_profiles_emergency_stop', 'idx_risk_profiles_risk_level',
        'idx_api_credentials_account_id', 'idx_api_credentials_active', 'idx_api_credentials_last_used',
        'idx_trade_signals_account_id', 'idx_trade_signals_symbol', 'idx_trade_signals_strategy',
        'idx_trade_signals_status', 'idx_trade_signals_created_at', 'idx_trade_signals_expires_at',
        'idx_order_status_trade_id', 'idx_order_status_order_id', 'idx_order_status_status',
        'idx_order_status_timestamp',
        # Composite indexes
        'idx_positions_account_status', 'idx_trades_account_status', 'idx_trades_symbol_status',
        'idx_signals_account_strategy', 'idx_signals_symbol_status'
    ]
    
    for index in indexes:
        try:
            op.drop_index(index)
        except Exception:
            # Index might not exist, continue
            pass
