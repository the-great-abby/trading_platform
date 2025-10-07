"""add mock api credentials

Revision ID: 20251006_add_mock_api_credentials
Revises: 20251006_create_live_trading_account
Create Date: 2025-10-06 21:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
from datetime import datetime, timedelta

# revision identifiers, used by Alembic.
revision = '20251006_add_mock_api_credentials'
down_revision = None  # Can run independently
branch_labels = None
depends_on = None


def upgrade():
    """Add mock API credentials for testing."""
    
    conn = op.get_bind()
    
    # Check if api_credentials table exists, if not create it
    inspector = sa.inspect(conn)
    
    if 'api_credentials' not in inspector.get_table_names():
        # Create api_credentials table
        op.create_table(
            'api_credentials',
            sa.Column('credential_id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('encrypted_api_key', sa.Text, nullable=False),
            sa.Column('encrypted_api_secret', sa.Text, nullable=False),
            sa.Column('access_token', sa.Text),
            sa.Column('refresh_token', sa.Text),
            sa.Column('token_expires_at', sa.DateTime),
            sa.Column('is_active', sa.Boolean, nullable=False, default=True),
            sa.Column('last_used_at', sa.DateTime),
            sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
        )
    
    # Insert mock credentials for the default account
    # Note: These are mock/placeholder values - replace with real credentials via auth endpoint
    conn.execute(sa.text("""
        INSERT INTO api_credentials (
            credential_id,
            account_id,
            encrypted_api_key,
            encrypted_api_secret,
            access_token,
            refresh_token,
            token_expires_at,
            is_active,
            last_used_at,
            created_at,
            updated_at
        ) VALUES (
            gen_random_uuid(),
            '19c25392-8b61-4b71-a344-0eb04d275528',
            'mock_encrypted_api_key',
            'mock_encrypted_api_secret',
            'mock_access_token_placeholder',
            'mock_refresh_token_placeholder',
            NOW() + INTERVAL '24 hours',
            true,
            NOW(),
            NOW(),
            NOW()
        )
        ON CONFLICT DO NOTHING;
    """))


def downgrade():
    """Remove mock API credentials."""
    
    conn = op.get_bind()
    
    # Delete mock credentials
    conn.execute(sa.text("""
        DELETE FROM api_credentials
        WHERE encrypted_api_key = 'mock_encrypted_api_key';
    """))





