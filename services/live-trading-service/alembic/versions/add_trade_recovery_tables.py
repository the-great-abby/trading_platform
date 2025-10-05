"""
Database migration for trade recovery tables
Adds recovery functionality to existing Live Trading Service database
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_trade_recovery_tables'
down_revision = 'previous_revision'  # Update this to the latest revision
branch_labels = None
depends_on = None


def upgrade():
    """Add trade recovery tables"""
    
    # Create active_trades table
    op.create_table('active_trades',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('account_id', sa.String(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('side', sa.String(), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('entry_price', sa.Float(), nullable=False),
        sa.Column('current_price', sa.Float(), nullable=True),
        sa.Column('unrealized_pnl', sa.Float(), nullable=True),
        sa.Column('entry_time', sa.DateTime(), nullable=False),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_active_trades_account_id'), 'active_trades', ['account_id'], unique=False)
    
    # Create recovery_sessions table
    op.create_table('recovery_sessions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('account_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('recovery_type', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('total_trades_detected', sa.Integer(), nullable=False),
        sa.Column('trades_processed', sa.Integer(), nullable=False),
        sa.Column('trades_assigned', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recovery_sessions_account_id'), 'recovery_sessions', ['account_id'], unique=False)
    
    # Create strategy_assignments table
    op.create_table('strategy_assignments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('trade_id', sa.String(), nullable=False),
        sa.Column('strategy_id', sa.String(), nullable=False),
        sa.Column('strategy_name', sa.String(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('assignment_reason', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('auto_assigned', sa.Boolean(), nullable=False),
        sa.Column('user_confirmed', sa.Boolean(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), nullable=False),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('rejected_at', sa.DateTime(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['recovery_sessions.id'], ),
        sa.ForeignKeyConstraint(['trade_id'], ['active_trades.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_strategy_assignments_session_id'), 'strategy_assignments', ['session_id'], unique=False)
    op.create_index(op.f('ix_strategy_assignments_trade_id'), 'strategy_assignments', ['trade_id'], unique=False)
    
    # Create recovery_logs table
    op.create_table('recovery_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('level', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['recovery_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recovery_logs_session_id'), 'recovery_logs', ['session_id'], unique=False)


def downgrade():
    """Remove trade recovery tables"""
    
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_index(op.f('ix_recovery_logs_session_id'), table_name='recovery_logs')
    op.drop_table('recovery_logs')
    
    op.drop_index(op.f('ix_strategy_assignments_trade_id'), table_name='strategy_assignments')
    op.drop_index(op.f('ix_strategy_assignments_session_id'), table_name='strategy_assignments')
    op.drop_table('strategy_assignments')
    
    op.drop_index(op.f('ix_recovery_sessions_account_id'), table_name='recovery_sessions')
    op.drop_table('recovery_sessions')
    
    op.drop_index(op.f('ix_active_trades_account_id'), table_name='active_trades')
    op.drop_table('active_trades')








