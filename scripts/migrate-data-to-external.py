#!/usr/bin/env python3
"""
Data Migration Script: Current TimescaleDB → External Databases
Migrates data from current trading-system database to new external databases
"""

import psycopg2
import psycopg2.extras
import json
import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import argparse
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/data-migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str
    port: int
    database: str
    user: str
    password: str
    
    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

class DataMigrator:
    """Main data migration class"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        
        # Source database (current - using port forwarding)
        self.source_db = DatabaseConfig(
            host="localhost",
            port=11140,
            database="trading_bot",
            user="trading_user",
            password="trading_pass"
        )
        
        # Target external databases (using port forwarding)
        self.target_dbs = {
            "timescale": DatabaseConfig(
                host="localhost",
                port=11150,
                database="trading",
                user="postgres",
                password="postgres"
            ),
            "vector": DatabaseConfig(
                host="localhost",
                port=11151,
                database="trading",
                user="postgres",
                password="postgres"
            ),
            "age": DatabaseConfig(
                host="localhost",
                port=11152,
                database="trading",
                user="postgres",
                password="postgres"
            ),
            "config": DatabaseConfig(
                host="localhost",
                port=11153,
                database="trading",
                user="postgres",
                password="postgres"
            )
        }
        
        # Migration statistics
        self.stats = {
            "tables_migrated": 0,
            "rows_migrated": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None
        }
        
        # Table mapping: source_table -> target_database
        self.table_mapping = {
            # Core trading data → TimescaleDB External
            "trades": "timescale",
            "historical_prices": "timescale",
            "backtest_runs": "timescale",
            "backtest_trades": "timescale",
            "backtest_equity_curves": "timescale",
            "signals": "timescale",
            "orders": "timescale",
            "positions": "timescale",
            "earnings_reports": "timescale",
            "historical_options_snapshots": "timescale",
            "options_contracts_cache": "timescale",
            "market_data": "timescale",
            "market_data_cache": "timescale",
            
            # Vector data → Vector Storage External
            "vector_embeddings": "vector",
            "vectorization_jobs": "vector",
            "vectorization_logs": "vector",
            "vectorization_metrics": "vector",
            "news_embeddings": "vector",
            
            # News data → Vector Storage (for semantic search)
            "historical_news": "vector",
            "news_cache": "vector",
            "news_historical": "vector",
            "news_articles": "vector",
            
            # Configuration data → Regular PostgreSQL
            "trading_config": "config",
            "popular_symbols": "config",
            "report_jobs": "config",
            "risk_metrics": "config",
            
            # Graph data → Apache AGE
            "trading_relationships": "age",
            "market_correlations": "age",
            "news_networks": "age"
        }
    
    def get_connection(self, db_config: DatabaseConfig) -> psycopg2.extensions.connection:
        """Get database connection"""
        try:
            conn = psycopg2.connect(
                host=db_config.host,
                port=db_config.port,
                database=db_config.database,
                user=db_config.user,
                password=db_config.password,
                connect_timeout=30
            )
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to {db_config.database}: {e}")
            raise
    
    def test_connections(self) -> bool:
        """Test all database connections"""
        logger.info("🔍 Testing database connections...")
        
        try:
            # Test source database
            with self.get_connection(self.source_db) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
                    table_count = cur.fetchone()[0]
                    logger.info(f"✅ Source database: {table_count} tables found")
            
            # Test target databases
            for db_name, db_config in self.target_dbs.items():
                try:
                    with self.get_connection(db_config) as conn:
                        with conn.cursor() as cur:
                            cur.execute("SELECT version()")
                            version = cur.fetchone()[0]
                            logger.info(f"✅ {db_name} database: {version.split(',')[0]}")
                except Exception as e:
                    logger.error(f"❌ {db_name} database connection failed: {e}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return False
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get table schema information"""
        try:
            with self.get_connection(self.source_db) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT column_name, data_type, udt_name, is_nullable, column_default
                        FROM information_schema.columns 
                        WHERE table_name = %s AND table_schema = 'public'
                        ORDER BY ordinal_position
                    """, (table_name,))
                    
                    columns = []
                    for row in cur.fetchall():
                        column_name, data_type, udt_name, is_nullable, column_default = row
                        
                        # Handle custom types like vector
                        if data_type == 'USER-DEFINED':
                            if 'vector' in udt_name.lower():
                                # Extract vector dimensions from udt_name
                                if '128' in udt_name:
                                    actual_type = 'vector(128)'
                                elif '1536' in udt_name:
                                    actual_type = 'vector(1536)'
                                elif '10' in udt_name:
                                    actual_type = 'vector(10)'
                                else:
                                    actual_type = 'vector'
                            else:
                                actual_type = udt_name
                        else:
                            actual_type = data_type
                        
                        columns.append({
                            "name": column_name,
                            "type": actual_type,
                            "nullable": is_nullable == "YES",
                            "default": column_default
                        })
                    
                    return {"table_name": table_name, "columns": columns}
                    
        except Exception as e:
            logger.error(f"Failed to get schema for {table_name}: {e}")
            return {}
    
    def get_table_count(self, table_name: str) -> int:
        """Get row count for a table"""
        try:
            with self.get_connection(self.source_db) as conn:
                with conn.cursor() as cur:
                    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                    return cur.fetchone()[0]
        except Exception as e:
            logger.error(f"Failed to get count for {table_name}: {e}")
            return 0
    
    def migrate_table(self, table_name: str, target_db_name: str) -> bool:
        """Migrate a single table"""
        logger.info(f"🔄 Migrating {table_name} to {target_db_name}...")
        
        try:
            # Get table schema and count
            schema = self.get_table_schema(table_name)
            if not schema:
                logger.error(f"Failed to get schema for {table_name}")
                return False
            
            row_count = self.get_table_count(table_name)
            logger.info(f"📊 {table_name}: {row_count} rows to migrate")
            
            if row_count == 0:
                logger.info(f"⏭️ Skipping {table_name} (no data)")
                return True
            
            if self.dry_run:
                logger.info(f"🔍 DRY RUN: Would migrate {row_count} rows from {table_name}")
                return True
            
            # Get target database connection
            target_db = self.target_dbs[target_db_name]
            
            # Migrate data in batches
            batch_size = 1000
            offset = 0
            migrated_rows = 0
            
            with self.get_connection(self.source_db) as source_conn:
                with self.get_connection(target_db) as target_conn:
                    
                    while offset < row_count:
                        # Read batch from source
                        with source_conn.cursor() as source_cur:
                            source_cur.execute(f"SELECT * FROM {table_name} LIMIT {batch_size} OFFSET {offset}")
                            batch = source_cur.fetchall()
                        
                        if not batch:
                            break
                        
                        # Get column names
                        with source_conn.cursor() as cur:
                            cur.execute(f"SELECT * FROM {table_name} LIMIT 0")
                            column_names = [desc[0] for desc in cur.description]
                        
                        # Insert batch into target
                        with target_conn.cursor() as target_cur:
                            # Create placeholders for INSERT
                            placeholders = ','.join(['%s'] * len(column_names))
                            columns = ','.join(column_names)
                            
                            # Batch insert
                            insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                            psycopg2.extras.execute_batch(target_cur, insert_query, batch)
                        
                        target_conn.commit()
                        migrated_rows += len(batch)
                        offset += batch_size
                        
                        logger.info(f"📦 {table_name}: {migrated_rows}/{row_count} rows migrated")
                    
                    logger.info(f"✅ {table_name}: {migrated_rows} rows migrated successfully")
                    self.stats["rows_migrated"] += migrated_rows
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Failed to migrate {table_name}: {e}")
            self.stats["errors"] += 1
            return False
    
    def create_target_tables(self) -> bool:
        """Create tables in target databases based on source schemas"""
        logger.info("🔨 Creating target tables...")
        
        try:
            for table_name, target_db_name in self.table_mapping.items():
                if target_db_name not in self.target_dbs:
                    logger.warning(f"⚠️ Unknown target database {target_db_name} for {table_name}")
                    continue
                
                logger.info(f"🔨 Creating {table_name} in {target_db_name}...")
                
                if self.dry_run:
                    logger.info(f"🔍 DRY RUN: Would create {table_name} in {target_db_name}")
                    continue
                
                # Get source schema
                schema = self.get_table_schema(table_name)
                if not schema:
                    logger.warning(f"⚠️ Could not get schema for {table_name}, skipping")
                    continue
                
                # Create table in target
                target_db = self.target_dbs[target_db_name]
                with self.get_connection(target_db) as conn:
                    with conn.cursor() as cur:
                        # Build CREATE TABLE statement
                        columns = []
                        for col in schema["columns"]:
                            # Simplify column types and handle sequences
                            col_type = col['type']
                            col_name = col['name']
                            
                            # Convert integer columns with sequences to SERIAL
                            if (col_type == 'integer' and 
                                col["default"] and 
                                "nextval" in str(col["default"]) and
                                col_name == 'id'):
                                col_def = f"{col_name} SERIAL"
                            else:
                                # Handle custom types
                                if col_type == 'vector(128)':
                                    col_def = f"{col_name} vector(128)"
                                elif col_type == 'vector(1536)':
                                    col_def = f"{col_name} vector(1536)"
                                elif col_type == 'vector(10)':
                                    col_def = f"{col_name} vector(10)"
                                else:
                                    col_def = f"{col_name} {col_type}"
                                
                                if not col["nullable"]:
                                    col_def += " NOT NULL"
                                # Skip complex defaults for now
                        
                            columns.append(col_def)
                        
                        create_sql = f"""
                            CREATE TABLE IF NOT EXISTS {table_name} (
                                {', '.join(columns)}
                            )
                        """
                        
                        cur.execute(create_sql)
                        conn.commit()
                        
                        logger.info(f"✅ Created table {table_name} in {target_db_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create target tables: {e}")
            return False
    
    def migrate_all_data(self) -> bool:
        """Migrate all data according to table mapping"""
        logger.info("🚀 Starting data migration...")
        
        self.stats["start_time"] = datetime.now()
        
        try:
            # Create target tables first
            if not self.create_target_tables():
                logger.error("Failed to create target tables")
                return False
            
            # Migrate each table
            for table_name, target_db_name in self.table_mapping.items():
                if self.migrate_table(table_name, target_db_name):
                    self.stats["tables_migrated"] += 1
                else:
                    logger.error(f"Failed to migrate {table_name}")
                    # Continue with other tables
            
            self.stats["end_time"] = datetime.now()
            
            # Print summary
            self.print_migration_summary()
            
            return self.stats["errors"] == 0
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False
    
    def print_migration_summary(self):
        """Print migration summary"""
        duration = self.stats["end_time"] - self.stats["start_time"]
        
        logger.info("=" * 60)
        logger.info("📊 MIGRATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Tables migrated: {self.stats['tables_migrated']}")
        logger.info(f"Rows migrated: {self.stats['rows_migrated']:,}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info(f"Duration: {duration}")
        logger.info(f"Status: {'✅ SUCCESS' if self.stats['errors'] == 0 else '❌ FAILED'}")
        logger.info("=" * 60)
    
    def validate_migration(self) -> bool:
        """Validate that migration was successful"""
        logger.info("🔍 Validating migration...")
        
        try:
            validation_errors = 0
            
            for table_name, target_db_name in self.table_mapping.items():
                # Get source count
                source_count = self.get_table_count(table_name)
                
                # Get target count
                target_db = self.target_dbs[target_db_name]
                with self.get_connection(target_db) as conn:
                    with conn.cursor() as cur:
                        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                        target_count = cur.fetchone()[0]
                
                if source_count != target_count:
                    logger.error(f"❌ {table_name}: Source={source_count}, Target={target_count}")
                    validation_errors += 1
                else:
                    logger.info(f"✅ {table_name}: {source_count} rows validated")
            
            if validation_errors == 0:
                logger.info("🎉 All tables validated successfully!")
                return True
            else:
                logger.error(f"❌ {validation_errors} tables failed validation")
                return False
                
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Migrate data to external databases")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated without actually doing it")
    parser.add_argument("--validate-only", action="store_true", help="Only validate existing migration")
    parser.add_argument("--create-tables-only", action="store_true", help="Only create target tables")
    parser.add_argument("--test-connections", action="store_true", help="Only test database connections")
    
    args = parser.parse_args()
    
    # Create migrator
    migrator = DataMigrator(dry_run=args.dry_run)
    
    try:
        if args.test_connections:
            if migrator.test_connections():
                logger.info("✅ All connections successful")
                return 0
            else:
                logger.error("❌ Some connections failed")
                return 1
        
        if args.create_tables_only:
            if migrator.create_target_tables():
                logger.info("✅ Target tables created successfully")
                return 0
            else:
                logger.error("❌ Failed to create target tables")
                return 1
        
        if args.validate_only:
            if migrator.validate_migration():
                logger.info("✅ Migration validation successful")
                return 0
            else:
                logger.error("❌ Migration validation failed")
                return 1
        
        # Full migration
        if not migrator.test_connections():
            logger.error("❌ Database connections failed")
            return 1
        
        if migrator.migrate_all_data():
            logger.info("🎉 Data migration completed successfully!")
            
            # Validate migration
            if migrator.validate_migration():
                logger.info("✅ Migration validation successful")
                return 0
            else:
                logger.error("❌ Migration validation failed")
                return 1
        else:
            logger.error("❌ Data migration failed")
            return 1
            
    except KeyboardInterrupt:
        logger.info("⏹️ Migration interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
