"""
Partition tables by symbol for performance
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250711_partition_tables_by_symbol'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # 1. Create new partitioned table
    op.execute('''
        CREATE TABLE historical_prices_partitioned (
            symbol VARCHAR(10) NOT NULL,
            date DATE NOT NULL,
            open_price DOUBLE PRECISION NOT NULL,
            high_price DOUBLE PRECISION NOT NULL,
            low_price DOUBLE PRECISION NOT NULL,
            close_price DOUBLE PRECISION NOT NULL,
            volume INTEGER NOT NULL,
            provider VARCHAR(50) NOT NULL,
            interval VARCHAR(10) NOT NULL,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            PRIMARY KEY (symbol, date)
        ) PARTITION BY LIST (symbol);
    ''')
    # 2. Create example partitions
    op.execute("""
        CREATE TABLE historical_prices_aapl PARTITION OF historical_prices_partitioned FOR VALUES IN ('AAPL');
        CREATE TABLE historical_prices_msft PARTITION OF historical_prices_partitioned FOR VALUES IN ('MSFT');
        CREATE TABLE historical_prices_goog PARTITION OF historical_prices_partitioned FOR VALUES IN ('GOOG');
        CREATE TABLE historical_prices_default PARTITION OF historical_prices_partitioned DEFAULT;
        -- Add more partitions for other symbols as needed
    """)
    # 3. Copy data
    op.execute('''
        INSERT INTO historical_prices_partitioned
        SELECT * FROM historical_prices;
    ''')
    # 4. Drop old table
    op.execute('''
        DROP TABLE historical_prices;
    ''')
    # 5. Rename new table
    op.execute('''
        ALTER TABLE historical_prices_partitioned RENAME TO historical_prices;
    ''')
    # 6. Recreate indexes
    op.execute('''
        CREATE INDEX idx_date_range ON historical_prices (date);
        CREATE INDEX idx_provider_symbol ON historical_prices (provider, symbol);
        CREATE INDEX idx_symbol_date ON historical_prices (symbol, date);
    ''')

def downgrade():
    # Cannot easily unpartition in-place; user must recreate tables if needed
    pass 