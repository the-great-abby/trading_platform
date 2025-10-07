"""create live trading account

Revision ID: 20251006_create_live_trading_account
Revises: 20250927_add_strategy_management_tables
Create Date: 2025-10-06 21:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '20251006_create_live_trading_account'
down_revision = None  # Can run independently
branch_labels = None
depends_on = None


def upgrade():
    """Create the live trading account record."""
    
    # Check if the live_trading_accounts table exists
    # If not, create it first
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    if 'live_trading_accounts' not in inspector.get_table_names():
        # Create enum types if they don't exist
        conn.execute(sa.text("""
            DO $$ BEGIN
                CREATE TYPE accounttype AS ENUM ('CASH', 'MARGIN');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))
        
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
    
    # Insert the default live trading account
    # Using the account ID that the live trading monitor expects
    conn.execute(sa.text("""
        INSERT INTO live_trading_accounts (
            account_id,
            public_account_id,
            account_name,
            account_type,
            buying_power,
            cash_balance,
            equity,
            is_active,
            created_at,
            updated_at
        ) VALUES (
            '19c25392-8b61-4b71-a344-0eb04d275528',
            '19c25392-8b61-4b71-a344-0eb04d275528',
            'Default Live Trading Account',
            'CASH',
            10000.00,
            10000.00,
            10000.00,
            true,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (public_account_id) DO UPDATE SET
            account_name = EXCLUDED.account_name,
            account_type = EXCLUDED.account_type,
            buying_power = EXCLUDED.buying_power,
            cash_balance = EXCLUDED.cash_balance,
            equity = EXCLUDED.equity,
            is_active = EXCLUDED.is_active,
            updated_at = CURRENT_TIMESTAMP;
    """))


def downgrade():
    """Remove the live trading account record."""
    
    conn = op.get_bind()
    
    # Delete the account
    conn.execute(sa.text("""
        DELETE FROM live_trading_accounts
        WHERE public_account_id = '19c25392-8b61-4b71-a344-0eb04d275528';
    """))

