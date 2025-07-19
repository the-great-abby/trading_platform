"""
Database Optimization System
Comprehensive database performance optimization and monitoring
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from contextlib import asynccontextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class QueryMetrics:
    """Query performance metrics"""
    query_hash: str
    query_text: str
    execution_time: float
    rows_returned: int
    timestamp: float
    table_scans: int
    index_usage: bool
    cache_hit: bool


@dataclass
class IndexRecommendation:
    """Database index recommendation"""
    table_name: str
    column_name: str
    index_type: str  # 'btree', 'gin', 'gist', 'hash'
    reason: str
    estimated_benefit: float
    creation_cost: float


class DatabaseOptimizer:
    """Comprehensive database optimization system"""
    
    def __init__(self, database_url: str, max_connections: int = 20):
        self.database_url = database_url
        self.max_connections = max_connections
        self.engine = None
        self.session_factory = None
        self.query_metrics: List[QueryMetrics] = []
        self.slow_query_threshold = 1.0  # seconds
        # Connection pooling configuration
        self.pool_config = {
            'pool_size': max_connections,
            'max_overflow': max_connections * 2,
            'pool_timeout': 30,
            'pool_recycle': 3600,  # Recycle connections every hour
            'pool_pre_ping': True,  # Test connections before use
            'echo': False  # Set to True for SQL logging
        }
        # Centralized, extendable list of required indexes
        self.required_indexes: List[Tuple[str, List[str], str]] = [
            # Historical Prices (Partitioned Table)
            ("historical_prices", ["symbol"], "btree"),
            ("historical_prices", ["symbol", "date"], "btree"),
            ("historical_prices", ["provider", "symbol"], "btree"),
            ("historical_prices", ["date"], "btree"),
            # Options Contracts Cache
            ("options_contracts_cache", ["symbol"], "btree"),
            ("options_contracts_cache", ["symbol", "expiration"], "btree"),
            ("options_contracts_cache", ["symbol", "expiration", "strike", "option_type"], "btree"),
            ("options_contracts_cache", ["expiration"], "btree"),
            ("options_contracts_cache", ["cache_date"], "btree"),
            # Backtest Tables
            ("backtest_trades", ["symbol"], "btree"),
            ("backtest_trades", ["run_id"], "btree"),
            ("backtest_trades", ["timestamp"], "btree"),
            ("backtest_trades", ["action"], "btree"),
            ("backtest_trades", ["run_id", "timestamp"], "btree"),
            ("backtest_runs", ["run_id"], "btree"),
            ("backtest_runs", ["strategy_name"], "btree"),
            ("backtest_runs", ["created_at"], "btree"),
            ("backtest_runs", ["start_date", "end_date"], "btree"),
            ("backtest_equity_curves", ["run_id"], "btree"),
            ("backtest_equity_curves", ["date"], "btree"),
            ("backtest_equity_curves", ["run_id", "date"], "btree"),
            # News Tables
            ("historical_news", ["ticker"], "btree"),
            ("historical_news", ["published_at"], "btree"),
            ("historical_news", ["sentiment_score"], "btree"),
            ("historical_news", ["impact_score"], "btree"),
            ("historical_news", ["event_type"], "btree"),
            ("historical_news", ["source"], "btree"),
            ("historical_news", ["ticker", "published_at"], "btree"),
            # Cache Tables
            ("market_data_cache", ["symbol"], "btree"),
            ("market_data_cache", ["provider"], "btree"),
            ("market_data_cache", ["symbol", "provider"], "btree"),
            ("news_cache", ["symbol"], "btree"),
            ("news_cache", ["source"], "btree"),
            ("news_cache", ["symbol", "source"], "btree"),
        ]

    def _ensure_engine_and_session_factory(self):
        if self.engine is None:
            self.engine = create_engine(
                self.database_url,
                **self.pool_config
            )
        if self.session_factory is None:
            self.session_factory = sessionmaker(bind=self.engine)

    def add_required_index(self, table: str, columns: List[str], index_type: str = "btree"):
        """Add a custom required index to the optimizer."""
        self.required_indexes.append((table, columns, index_type))
        logger.info(f"Added custom required index: {table}({columns}) type={index_type}")

    async def ensure_indexes(self):
        """Ensure all required indexes exist for key tables and columns"""
        try:
            self._ensure_engine_and_session_factory()
            with self.engine.connect() as conn:
                created_count = 0
                existing_count = 0
                for table, columns, index_type in self.required_indexes:
                    index_name = f"idx_{table}_{'_'.join(columns)}"
                    columns_str = ', '.join(columns)
                    # Check if index already exists
                    index_exists = await self._check_index_exists(conn, table, columns[0])
                    if not index_exists:
                        sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} USING {index_type} ({columns_str})"
                        try:
                            conn.execute(text(sql))
                            logger.info(f"✅ Created index: {index_name} on {table}({columns_str})")
                            created_count += 1
                        except Exception as e:
                            logger.warning(f"⚠️  Failed to create index {index_name}: {e}")
                    else:
                        existing_count += 1
                        logger.debug(f"📋 Index already exists: {index_name}")
                conn.commit()
                logger.info(f"✅ Index creation completed: {created_count} created, {existing_count} already existed")
        except Exception as e:
            logger.error(f"❌ Error ensuring indexes: {e}")

    async def initialize(self):
        """Initialize database connection with optimizations and ensure indexes"""
        try:
            self._ensure_engine_and_session_factory()
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✅ Database optimizer initialized successfully")
            # Run initial optimizations
            await self._run_initial_optimizations()
            # Ensure indexes
            await self.ensure_indexes()
        except Exception as e:
            logger.error(f"❌ Database optimizer initialization failed: {e}")
            raise
    
    async def _run_initial_optimizations(self):
        """Run initial database optimizations"""
        logger.info("🔧 Running initial database optimizations...")
        
        # Analyze tables
        await self.analyze_tables()
        
        # Check for missing indexes
        missing_indexes = await self.find_missing_indexes()
        if missing_indexes:
            logger.info(f"📊 Found {len(missing_indexes)} missing indexes")
            for idx in missing_indexes[:5]:  # Show first 5
                logger.info(f"   • {idx.table_name}.{idx.column_name} ({idx.reason})")
        
        # Optimize query planner
        await self.optimize_query_planner()
        
        # Set optimal PostgreSQL parameters
        await self.set_optimal_parameters()
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session with automatic cleanup"""
        self._ensure_engine_and_session_factory()
        session = self.session_factory()
        try:
            yield session
        finally:
            session.close()
    
    async def analyze_tables(self):
        """Analyze all tables for query optimization"""
        try:
            self._ensure_engine_and_session_factory()
            with self.engine.connect() as conn:
                # Get all table names
                inspector = inspect(self.engine)
                table_names = inspector.get_table_names()
                
                for table_name in table_names:
                    # Analyze table
                    conn.execute(text(f"ANALYZE {table_name}"))
                    logger.info(f"📊 Analyzed table: {table_name}")
                
                conn.commit()
                logger.info("✅ Table analysis completed")
                
        except Exception as e:
            logger.error(f"❌ Table analysis failed: {e}")
    
    async def find_missing_indexes(self) -> List[IndexRecommendation]:
        """Find missing indexes based on query patterns"""
        recommendations = []
        
        try:
            self._ensure_engine_and_session_factory()
            with self.engine.connect() as conn:
                # Check for common query patterns
                common_patterns = [
                    ("historical_prices", "symbol", "btree", "Symbol lookups"),
                    ("historical_prices", "date", "btree", "Date range queries"),
                    ("historical_prices", "symbol,date", "btree", "Symbol+date lookups"),
                    ("backtest_trades", "run_id", "btree", "Backtest result queries"),
                    ("backtest_trades", "timestamp", "btree", "Time-based trade queries"),
                    ("historical_news", "published_at", "btree", "News time queries"),
                    ("historical_news", "ticker", "btree", "News symbol queries"),
                    ("historical_news", "sentiment_score", "btree", "Sentiment analysis"),
                ]
                
                for table_name, column_name, index_type, reason in common_patterns:
                    # Check if index exists
                    index_exists = await self._check_index_exists(conn, table_name, column_name)
                    
                    if not index_exists:
                        recommendations.append(IndexRecommendation(
                            table_name=table_name,
                            column_name=column_name,
                            index_type=index_type,
                            reason=reason,
                            estimated_benefit=0.8,  # High benefit for common queries
                            creation_cost=0.1  # Low cost for simple indexes
                        ))
        
        except Exception as e:
            logger.error(f"❌ Index analysis failed: {e}")
        
        return recommendations
    
    async def _check_index_exists(self, conn, table_name: str, column_name: str) -> bool:
        """Check if an index exists on a table column"""
        try:
            result = conn.execute(text(f"""
                SELECT 1 FROM pg_indexes 
                WHERE tablename = '{table_name}' 
                AND indexdef LIKE '%{column_name}%'
            """))
            return result.fetchone() is not None
        except Exception:
            return False
    
    async def create_recommended_indexes(self, recommendations: List[IndexRecommendation]):
        """Create recommended indexes"""
        try:
            self._ensure_engine_and_session_factory()
            with self.engine.connect() as conn:
                for rec in recommendations:
                    try:
                        # Create index
                        index_name = f"idx_{rec.table_name}_{rec.column_name.replace(',', '_')}"
                        sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {rec.table_name} USING {rec.index_type} ({rec.column_name})"
                        
                        conn.execute(text(sql))
                        logger.info(f"✅ Created index: {index_name}")
                        
                    except Exception as e:
                        logger.warning(f"⚠️  Failed to create index for {rec.table_name}.{rec.column_name}: {e}")
                
                conn.commit()
                logger.info("✅ Index creation completed")
                
        except Exception as e:
            logger.error(f"❌ Index creation failed: {e}")
    
    async def optimize_query_planner(self):
        """Optimize PostgreSQL query planner settings"""
        try:
            self._ensure_engine_and_session_factory()
            with self.engine.connect() as conn:
                # Set optimal planner settings
                optimizations = [
                    "SET random_page_cost = 1.1",  # Optimize for SSD
                    "SET effective_cache_size = '4GB'",  # Adjust based on available RAM
                    "SET work_mem = '256MB'",  # Increase work memory
                    "SET maintenance_work_mem = '512MB'",  # Increase maintenance memory
                    "SET shared_preload_libraries = 'pg_stat_statements'",  # Enable query statistics
                ]
                
                for optimization in optimizations:
                    try:
                        conn.execute(text(optimization))
                    except Exception as e:
                        logger.warning(f"⚠️  Failed to apply optimization {optimization}: {e}")
                
                conn.commit()
                logger.info("✅ Query planner optimization completed")
                
        except Exception as e:
            logger.error(f"❌ Query planner optimization failed: {e}")
    
    async def set_optimal_parameters(self):
        """Set optimal PostgreSQL parameters for trading workloads"""
        try:
            self._ensure_engine_and_session_factory()
            with self.engine.connect() as conn:
                # Trading-specific optimizations
                trading_optimizations = [
                    "SET max_connections = 200",
                    "SET shared_buffers = '1GB'",
                    "SET effective_cache_size = '4GB'",
                    "SET maintenance_work_mem = '512MB'",
                    "SET checkpoint_completion_target = 0.9",
                    "SET wal_buffers = '16MB'",
                    "SET default_statistics_target = 100",
                    "SET random_page_cost = 1.1",
                    "SET effective_io_concurrency = 200",
                ]
                
                for optimization in trading_optimizations:
                    try:
                        conn.execute(text(optimization))
                    except Exception as e:
                        logger.warning(f"⚠️  Failed to apply parameter {optimization}: {e}")
                
                conn.commit()
                logger.info("✅ Trading-specific parameters set")
                
        except Exception as e:
            logger.error(f"❌ Parameter optimization failed: {e}")
    
    async def monitor_query_performance(self, query_text: str, execution_time: float, 
                                      rows_returned: int, cache_hit: bool = False):
        """Monitor and track query performance"""
        query_hash = hash(query_text)
        
        metrics = QueryMetrics(
            query_hash=query_hash,
            query_text=query_text,
            execution_time=execution_time,
            rows_returned=rows_returned,
            timestamp=time.time(),
            table_scans=0,  # Would need to parse EXPLAIN for this
            index_usage=True,  # Would need to parse EXPLAIN for this
            cache_hit=cache_hit
        )
        
        self.query_metrics.append(metrics)
        
        # Alert on slow queries
        if execution_time > self.slow_query_threshold:
            logger.warning(f"🐌 Slow query detected: {execution_time:.2f}s")
            logger.warning(f"   Query: {query_text[:100]}...")
            logger.warning(f"   Rows: {rows_returned}")
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Generate database performance report"""
        if not self.query_metrics:
            return {"message": "No query metrics available"}
        
        # Calculate statistics
        execution_times = [m.execution_time for m in self.query_metrics]
        avg_time = np.mean(execution_times)
        max_time = np.max(execution_times)
        min_time = np.min(execution_times)
        
        # Find slowest queries
        slowest_queries = sorted(self.query_metrics, 
                               key=lambda x: x.execution_time, 
                               reverse=True)[:5]
        
        # Calculate cache hit rate
        cache_hits = sum(1 for m in self.query_metrics if m.cache_hit)
        cache_hit_rate = (cache_hits / len(self.query_metrics)) * 100 if self.query_metrics else 0
        
        return {
            "total_queries": len(self.query_metrics),
            "average_execution_time": avg_time,
            "max_execution_time": max_time,
            "min_execution_time": min_time,
            "cache_hit_rate": cache_hit_rate,
            "slowest_queries": [
                {
                    "query": q.query_text[:100] + "..." if len(q.query_text) > 100 else q.query_text,
                    "execution_time": q.execution_time,
                    "rows_returned": q.rows_returned
                }
                for q in slowest_queries
            ]
        }
    
    async def optimize_queries(self) -> List[str]:
        """Analyze and suggest query optimizations"""
        optimizations = []
        
        # Analyze query patterns
        query_patterns = {}
        for metric in self.query_metrics:
            # Extract table names from query (simplified)
            if "historical_prices" in metric.query_text:
                query_patterns["historical_prices"] = query_patterns.get("historical_prices", 0) + 1
            if "backtest_trades" in metric.query_text:
                query_patterns["backtest_trades"] = query_patterns.get("backtest_trades", 0) + 1
        
        # Suggest optimizations based on patterns
        for table, count in query_patterns.items():
            if count > 10:  # Frequently accessed table
                optimizations.append(f"Consider partitioning {table} by date for better performance")
                optimizations.append(f"Add covering indexes for common {table} queries")
        
        # Suggest based on slow queries
        slow_queries = [m for m in self.query_metrics if m.execution_time > 1.0]
        if slow_queries:
            optimizations.append(f"Found {len(slow_queries)} slow queries - consider query optimization")
        
        return optimizations
    
    async def vacuum_and_analyze(self):
        """Run VACUUM and ANALYZE for table maintenance"""
        try:
            self._ensure_engine_and_session_factory()
            with self.engine.connect() as conn:
                inspector = inspect(self.engine)
                table_names = inspector.get_table_names()
                
                for table_name in table_names:
                    # VACUUM table
                    conn.execute(text(f"VACUUM ANALYZE {table_name}"))
                    logger.info(f"🧹 VACUUM ANALYZE completed for {table_name}")
                
                conn.commit()
                logger.info("✅ Table maintenance completed")
                
        except Exception as e:
            logger.error(f"❌ Table maintenance failed: {e}")
    
    async def get_table_statistics(self) -> Dict[str, Any]:
        """Get database table statistics"""
        try:
            self._ensure_engine_and_session_factory()
            with self.engine.connect() as conn:
                stats = {}
                
                # Get table sizes
                result = conn.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        attname,
                        n_distinct,
                        correlation
                    FROM pg_stats 
                    WHERE schemaname = 'public'
                    ORDER BY tablename, attname
                """))
                
                for row in result:
                    table_name = row[1]
                    if table_name not in stats:
                        stats[table_name] = {}
                    
                    stats[table_name][row[2]] = {
                        "n_distinct": row[3],
                        "correlation": row[4]
                    }
                
                return stats
                
        except Exception as e:
            logger.error(f"❌ Failed to get table statistics: {e}")
            return {}


# Global database optimizer instance
db_optimizer = DatabaseOptimizer("postgresql://trading_user:trading_password@localhost:5432/trading_db")


async def get_db_optimizer() -> DatabaseOptimizer:
    """Get the global database optimizer instance"""
    return db_optimizer


async def optimize_database():
    """Run comprehensive database optimization"""
    optimizer = await get_db_optimizer()
    await optimizer.initialize()
    
    # Find and create missing indexes
    recommendations = await optimizer.find_missing_indexes()
    if recommendations:
        await optimizer.create_recommended_indexes(recommendations)
    
    # Run maintenance
    await optimizer.vacuum_and_analyze()
    
    # Get performance report
    report = await optimizer.get_performance_report()
    logger.info("📊 Database optimization completed")
    logger.info(f"   Total queries: {report.get('total_queries', 0)}")
    logger.info(f"   Average execution time: {report.get('average_execution_time', 0):.3f}s")
    logger.info(f"   Cache hit rate: {report.get('cache_hit_rate', 0):.1f}%") 