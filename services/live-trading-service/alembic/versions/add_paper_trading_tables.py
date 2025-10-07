"""Add paper trading tables

Revision ID: add_paper_trading_tables
Revises: add_trade_recovery_tables
Create Date: 2025-10-06 13:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_paper_trading_tables'
down_revision = 'add_trade_recovery_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Create paper_trading_orders table
    op.create_table('paper_trading_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.String(100), nullable=False),
        sa.Column('account_id', sa.String(100), nullable=False),
        sa.Column('symbol', sa.String(20), nullable=False),
        sa.Column('strategy', sa.String(50), nullable=False),
        sa.Column('order_type', sa.String(20), nullable=False),
        sa.Column('total_quantity', sa.Integer(), nullable=False),
        sa.Column('estimated_premium', sa.Numeric(10, 2), nullable=False),
        sa.Column('estimated_risk', sa.Numeric(10, 2), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('filled_at', sa.DateTime(), nullable=True),
        sa.Column('filled_quantity', sa.Integer(), nullable=False),
        sa.Column('average_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('remaining_quantity', sa.Integer(), nullable=False),
        sa.Column('greeks_data', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id')
    )
    
    # Create paper_trading_order_legs table
    op.create_table('paper_trading_order_legs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.String(100), nullable=False),
        sa.Column('leg_number', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(10), nullable=False),
        sa.Column('option_type', sa.String(10), nullable=True),
        sa.Column('strike_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('expiration_date', sa.String(50), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('premium', sa.Numeric(10, 2), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_id'], ['paper_trading_orders.order_id'], ondelete='CASCADE')
    )
    
    # Create indexes for better performance
    op.create_index('idx_paper_trading_orders_account_id', 'paper_trading_orders', ['account_id'])
    op.create_index('idx_paper_trading_orders_created_at', 'paper_trading_orders', ['created_at'])
    op.create_index('idx_paper_trading_order_legs_order_id', 'paper_trading_order_legs', ['order_id'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_paper_trading_order_legs_order_id', table_name='paper_trading_order_legs')
    op.drop_index('idx_paper_trading_orders_created_at', table_name='paper_trading_orders')
    op.drop_index('idx_paper_trading_orders_account_id', table_name='paper_trading_orders')
    
    # Drop tables
    op.drop_table('paper_trading_order_legs')
    op.drop_table('paper_trading_orders')
