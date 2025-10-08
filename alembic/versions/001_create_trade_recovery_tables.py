"""Create trade recovery tables

Revision ID: 001
Revises: 
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create trade recovery tables"""
    
    # Create active_trades table
    op.create_table('active_trades',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', sa.String(length=255), nullable=False),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('side', sa.Enum('BUY', 'SELL', name='tradeside'), nullable=False),
        sa.Column('entry_price', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('current_price', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('current_value', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('unrealized_pnl', sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column('entry_date', sa.DateTime(), nullable=True),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.Column('position_type', sa.Enum('STOCK', 'OPTION', 'FUTURE', name='positiontype'), nullable=False),
        sa.Column('option_details', sa.JSON(), nullable=True),
        sa.Column('status', sa.Enum('DETECTED', 'ASSIGNED', 'MANAGED', 'CLOSED', name='tradestatus'), nullable=False, default='DETECTED'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for active_trades
    op.create_index('idx_account_detected', 'active_trades', ['account_id', 'detected_at'])
    op.create_index('idx_symbol_detected', 'active_trades', ['symbol', 'detected_at'])
    op.create_index('idx_account_id', 'active_trades', ['account_id'])
    op.create_index('idx_detected_at', 'active_trades', ['detected_at'])
    
    # Create recovery_sessions table
    op.create_table('recovery_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('account_id', sa.String(length=255), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.Enum('IN_PROGRESS', 'COMPLETED', 'FAILED', 'CANCELLED', name='sessionstatus'), nullable=False, default='IN_PROGRESS'),
        sa.Column('total_trades_detected', sa.Integer(), nullable=False, default=0),
        sa.Column('trades_processed', sa.Integer(), nullable=False, default=0),
        sa.Column('trades_assigned', sa.Integer(), nullable=False, default=0),
        sa.Column('error_message', sa.String(length=1000), nullable=True),
        sa.Column('recovery_type', sa.Enum('DATABASE_FAILURE', 'MANUAL_RECOVERY', 'SCHEDULED_RECOVERY', name='recoverytype'), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for recovery_sessions
    op.create_index('idx_account_started', 'recovery_sessions', ['account_id', 'started_at'])
    op.create_index('idx_status_started', 'recovery_sessions', ['status', 'started_at'])
    op.create_index('idx_account_id', 'recovery_sessions', ['account_id'])
    op.create_index('idx_started_at', 'recovery_sessions', ['started_at'])
    
    # Create strategy_assignments table
    op.create_table('strategy_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recovery_session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('active_trade_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('strategy_name', sa.String(length=255), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), nullable=False),
        sa.Column('assigned_by', sa.String(length=255), nullable=False),
        sa.Column('confidence_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('assignment_reason', sa.String(length=1000), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'ACTIVE', 'PAUSED', 'CANCELLED', name='assignmentstatus'), nullable=False, default='PENDING'),
        sa.Column('strategy_parameters', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for strategy_assignments
    op.create_index('idx_recovery_session', 'strategy_assignments', ['recovery_session_id'])
    op.create_index('idx_active_trade', 'strategy_assignments', ['active_trade_id'])
    op.create_index('idx_strategy_name', 'strategy_assignments', ['strategy_name'])
    op.create_index('idx_assigned_at', 'strategy_assignments', ['assigned_at'])
    
    # Create recovery_logs table
    op.create_table('recovery_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recovery_session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.Enum('TRADE_DETECTED', 'STRATEGY_ASSIGNED', 'TRADE_MANAGED', 'ERROR_OCCURRED', 'SESSION_STARTED', 'SESSION_COMPLETED', 'SESSION_FAILED', 'SESSION_CANCELLED', name='logaction'), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('trade_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('strategy_name', sa.String(length=255), nullable=True),
        sa.Column('severity', sa.Enum('INFO', 'WARNING', 'ERROR', 'CRITICAL', name='logseverity'), nullable=False, default='INFO'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for recovery_logs
    op.create_index('idx_session_timestamp', 'recovery_logs', ['recovery_session_id', 'timestamp'])
    op.create_index('idx_action_timestamp', 'recovery_logs', ['action', 'timestamp'])
    op.create_index('idx_severity_timestamp', 'recovery_logs', ['severity', 'timestamp'])
    op.create_index('idx_user_timestamp', 'recovery_logs', ['user_id', 'timestamp'])
    op.create_index('idx_recovery_session_id', 'recovery_logs', ['recovery_session_id'])
    op.create_index('idx_timestamp', 'recovery_logs', ['timestamp'])
    
    # Add foreign key constraints
    op.create_foreign_key('fk_strategy_assignments_recovery_session', 'strategy_assignments', 'recovery_sessions', ['recovery_session_id'], ['id'])
    op.create_foreign_key('fk_strategy_assignments_active_trade', 'strategy_assignments', 'active_trades', ['active_trade_id'], ['id'])
    op.create_foreign_key('fk_recovery_logs_recovery_session', 'recovery_logs', 'recovery_sessions', ['recovery_session_id'], ['id'])
    op.create_foreign_key('fk_recovery_logs_active_trade', 'recovery_logs', 'active_trades', ['trade_id'], ['id'])
    
    # Add check constraints
    op.create_check_constraint('ck_active_trades_quantity_positive', 'active_trades', 'quantity > 0')
    op.create_check_constraint('ck_active_trades_entry_price_positive', 'active_trades', 'entry_price > 0')
    op.create_check_constraint('ck_active_trades_current_price_positive', 'active_trades', 'current_price > 0')
    op.create_check_constraint('ck_strategy_assignments_confidence_score_range', 'strategy_assignments', 'confidence_score >= 0.0 AND confidence_score <= 1.0')
    op.create_check_constraint('ck_recovery_sessions_trades_processed_le_detected', 'recovery_sessions', 'trades_processed <= total_trades_detected')
    op.create_check_constraint('ck_recovery_sessions_trades_assigned_le_processed', 'recovery_sessions', 'trades_assigned <= trades_processed')
    
    # Add unique constraints
    op.create_unique_constraint('uq_active_trades_account_symbol_detected', 'active_trades', ['account_id', 'symbol', 'detected_at'])


def downgrade():
    """Drop trade recovery tables"""
    
    # Drop foreign key constraints
    op.drop_constraint('fk_recovery_logs_active_trade', 'recovery_logs', type_='foreignkey')
    op.drop_constraint('fk_recovery_logs_recovery_session', 'recovery_logs', type_='foreignkey')
    op.drop_constraint('fk_strategy_assignments_active_trade', 'strategy_assignments', type_='foreignkey')
    op.drop_constraint('fk_strategy_assignments_recovery_session', 'strategy_assignments', type_='foreignkey')
    
    # Drop check constraints
    op.drop_constraint('uq_active_trades_account_symbol_detected', 'active_trades', type_='unique')
    op.drop_constraint('ck_recovery_sessions_trades_assigned_le_processed', 'recovery_sessions', type_='check')
    op.drop_constraint('ck_recovery_sessions_trades_processed_le_detected', 'recovery_sessions', type_='check')
    op.drop_constraint('ck_strategy_assignments_confidence_score_range', 'strategy_assignments', type_='check')
    op.drop_constraint('ck_active_trades_current_price_positive', 'active_trades', type_='check')
    op.drop_constraint('ck_active_trades_entry_price_positive', 'active_trades', type_='check')
    op.drop_constraint('ck_active_trades_quantity_positive', 'active_trades', type_='check')
    
    # Drop tables
    op.drop_table('recovery_logs')
    op.drop_table('strategy_assignments')
    op.drop_table('recovery_sessions')
    op.drop_table('active_trades')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS logseverity')
    op.execute('DROP TYPE IF EXISTS logaction')
    op.execute('DROP TYPE IF EXISTS assignmentstatus')
    op.execute('DROP TYPE IF EXISTS recoverytype')
    op.execute('DROP TYPE IF EXISTS sessionstatus')
    op.execute('DROP TYPE IF EXISTS tradestatus')
    op.execute('DROP TYPE IF EXISTS positiontype')
    op.execute('DROP TYPE IF EXISTS tradeside')




















