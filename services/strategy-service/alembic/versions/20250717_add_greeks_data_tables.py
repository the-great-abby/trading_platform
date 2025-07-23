"""Add Greeks data tables

Revision ID: 20250717_add_greeks_data_tables
Revises: 20250711_partition_tables_by_symbol
Create Date: 2025-07-17 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250717_add_greeks_data_tables'
down_revision = '20250711_partition_tables_by_symbol'
branch_labels = None
depends_on = None


def upgrade():
    # Create historical_options_snapshots table
    op.create_table(
        'historical_options_snapshots',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('symbol', sa.String(length=10), nullable=False),
        sa.Column('strike', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('expiration', sa.Date(), nullable=False),
        sa.Column('option_type', sa.String(length=4), nullable=False),  # 'call' or 'put'
        sa.Column('delta', sa.Numeric(precision=8, scale=6), nullable=True),
        sa.Column('gamma', sa.Numeric(precision=8, scale=6), nullable=True),
        sa.Column('theta', sa.Numeric(precision=8, scale=6), nullable=True),
        sa.Column('vega', sa.Numeric(precision=8, scale=6), nullable=True),
        sa.Column('implied_volatility', sa.Numeric(precision=8, scale=6), nullable=True),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('volume', sa.Integer(), nullable=True),
        sa.Column('open_interest', sa.Integer(), nullable=True),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('idx_historical_options_symbol', 'historical_options_snapshots', ['symbol'])
    op.create_index('idx_historical_options_snapshot_date', 'historical_options_snapshots', ['snapshot_date'])
    op.create_index('idx_historical_options_expiration', 'historical_options_snapshots', ['expiration'])
    op.create_index('idx_historical_options_symbol_date', 'historical_options_snapshots', ['symbol', 'snapshot_date'])
    op.create_index('idx_historical_options_contract', 'historical_options_snapshots', 
                   ['symbol', 'strike', 'expiration', 'option_type'])
    
    # Create options_greeks_cache table for caching
    op.create_table(
        'options_greeks_cache',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('cache_key', sa.String(length=255), nullable=False),
        sa.Column('symbol', sa.String(length=10), nullable=False),
        sa.Column('strike', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('expiration', sa.Date(), nullable=False),
        sa.Column('option_type', sa.String(length=4), nullable=False),
        sa.Column('delta', sa.Numeric(precision=8, scale=6), nullable=True),
        sa.Column('gamma', sa.Numeric(precision=8, scale=6), nullable=True),
        sa.Column('theta', sa.Numeric(precision=8, scale=6), nullable=True),
        sa.Column('vega', sa.Numeric(precision=8, scale=6), nullable=True),
        sa.Column('implied_volatility', sa.Numeric(precision=8, scale=6), nullable=True),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('volume', sa.Integer(), nullable=True),
        sa.Column('open_interest', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cache_key')
    )
    
    # Create indexes for cache table
    op.create_index('idx_options_greeks_cache_key', 'options_greeks_cache', ['cache_key'])
    op.create_index('idx_options_greeks_cache_symbol', 'options_greeks_cache', ['symbol'])
    op.create_index('idx_options_greeks_cache_expires', 'options_greeks_cache', ['expires_at'])
    
    # Create options_contracts table for storing contract metadata
    op.create_table(
        'options_contracts',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('symbol', sa.String(length=10), nullable=False),
        sa.Column('strike', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('expiration', sa.Date(), nullable=False),
        sa.Column('option_type', sa.String(length=4), nullable=False),
        sa.Column('contract_id', sa.String(length=50), nullable=True),  # Polygon contract ID
        sa.Column('exercise_style', sa.String(length=10), nullable=True),  # 'american' or 'european'
        sa.Column('shares_per_contract', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('last_updated', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for contracts table
    op.create_index('idx_options_contracts_symbol', 'options_contracts', ['symbol'])
    op.create_index('idx_options_contracts_expiration', 'options_contracts', ['expiration'])
    op.create_index('idx_options_contracts_active', 'options_contracts', ['is_active'])
    op.create_index('idx_options_contracts_contract', 'options_contracts', 
                   ['symbol', 'strike', 'expiration', 'option_type'])


def downgrade():
    # Drop indexes first
    op.drop_index('idx_options_contracts_contract', table_name='options_contracts')
    op.drop_index('idx_options_contracts_active', table_name='options_contracts')
    op.drop_index('idx_options_contracts_expiration', table_name='options_contracts')
    op.drop_index('idx_options_contracts_symbol', table_name='options_contracts')
    
    op.drop_index('idx_options_greeks_cache_expires', table_name='options_greeks_cache')
    op.drop_index('idx_options_greeks_cache_symbol', table_name='options_greeks_cache')
    op.drop_index('idx_options_greeks_cache_key', table_name='options_greeks_cache')
    
    op.drop_index('idx_historical_options_contract', table_name='historical_options_snapshots')
    op.drop_index('idx_historical_options_symbol_date', table_name='historical_options_snapshots')
    op.drop_index('idx_historical_options_expiration', table_name='historical_options_snapshots')
    op.drop_index('idx_historical_options_snapshot_date', table_name='historical_options_snapshots')
    op.drop_index('idx_historical_options_symbol', table_name='historical_options_snapshots')
    
    # Drop tables
    op.drop_table('options_contracts')
    op.drop_table('options_greeks_cache')
    op.drop_table('historical_options_snapshots') 