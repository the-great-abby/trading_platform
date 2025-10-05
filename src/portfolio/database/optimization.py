"""
Database Performance Optimization
Advanced database optimization strategies and query performance tuning
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy import text, MetaData, Table, Index
from sqlalchemy.exc import SQLAlchemyError
import json

logger = logging.getLogger(__name__)

@dataclass
class QueryPerformanceMetrics:
    """Query performance metrics"""
    query_id: str
    query_text: str
    execution_time_ms: float
    rows_returned: int
    rows_examined: int
    index_usage: bool
    table_scans: bool
    temporary_tables: bool
    filesort: bool
    timestamp: datetime

@dataclass
class IndexRecommendation:
    """Database index recommendation"""
    table_name: str
    column_names: List[str]
    index_type: str  # B-tree, Hash, GIN, etc.
    reason: str
    estimated_benefit: str
    priority: int  # 1-5, 5 being highest

@dataclass
class OptimizationSuggestion:
    """Database optimization suggestion"""
    type: str  # INDEX, QUERY, CONFIG, SCHEMA
    title: str
    description: str
    impact: str  # HIGH, MEDIUM, LOW
    effort: str  # LOW, MEDIUM, HIGH
    sql_command: Optional[str] = None

class DatabaseOptimizer:
    """Advanced database performance optimizer"""
    
    def __init__(self, database_manager):
        self.database_manager = database_manager
        self.query_metrics: List[QueryPerformanceMetrics] = []
        self.optimization_history: List[Dict[str, Any]] = []
    
    async def analyze_query_performance(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Analyze slow queries and performance issues"""
        try:
            async with self.database_manager.get_session() as session:
                # Get slow queries from pg_stat_statements
                slow_queries_query = text("""
                    SELECT 
                        query,
                        calls,
                        total_time,
                        mean_time,
                        rows,
                        100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                    FROM pg_stat_statements 
                    WHERE mean_time > 100  -- Queries taking more than 100ms on average
                    ORDER BY mean_time DESC 
                    LIMIT :limit
                """)
                
                result = await session.execute(slow_queries_query, {"limit": limit})
                slow_queries = []
                
                for row in result:
                    slow_queries.append({
                        "query": row.query[:200] + "..." if len(row.query) > 200 else row.query,
                        "calls": row.calls,
                        "total_time_ms": round(row.total_time, 2),
                        "mean_time_ms": round(row.mean_time, 2),
                        "rows_returned": row.rows,
                        "cache_hit_percent": round(row.hit_percent, 2) if row.hit_percent else 0
                    })
                
                return slow_queries
                
        except Exception as e:
            logger.error(f"Error analyzing query performance: {e}")
            return []
    
    async def analyze_table_statistics(self) -> List[Dict[str, Any]]:
        """Analyze table statistics and identify optimization opportunities"""
        try:
            async with self.database_manager.get_session() as session:
                # Get table statistics
                table_stats_query = text("""
                    SELECT 
                        schemaname,
                        tablename,
                        attname as column_name,
                        n_distinct,
                        correlation,
                        most_common_vals,
                        most_common_freqs,
                        histogram_bounds
                    FROM pg_stats 
                    WHERE schemaname = 'public'
                    ORDER BY tablename, attname
                """)
                
                result = await session.execute(table_stats_query)
                table_stats = {}
                
                for row in result:
                    table_name = row.tablename
                    if table_name not in table_stats:
                        table_stats[table_name] = {
                            "table_name": table_name,
                            "columns": []
                        }
                    
                    table_stats[table_name]["columns"].append({
                        "column_name": row.column_name,
                        "distinct_values": row.n_distinct,
                        "correlation": round(row.correlation, 4) if row.correlation else None,
                        "most_common_values": row.most_common_vals,
                        "most_common_frequencies": row.most_common_freqs,
                        "has_histogram": bool(row.histogram_bounds)
                    })
                
                return list(table_stats.values())
                
        except Exception as e:
            logger.error(f"Error analyzing table statistics: {e}")
            return []
    
    async def analyze_index_usage(self) -> List[Dict[str, Any]]:
        """Analyze index usage and identify unused or inefficient indexes"""
        try:
            async with self.database_manager.get_session() as session:
                # Get index usage statistics
                index_usage_query = text("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_tup_read,
                        idx_tup_fetch,
                        idx_scan,
                        pg_size_pretty(pg_relation_size(indexrelid)) as index_size
                    FROM pg_stat_user_indexes 
                    WHERE schemaname = 'public'
                    ORDER BY idx_scan DESC
                """)
                
                result = await session.execute(index_usage_query)
                index_usage = []
                
                for row in result:
                    usage_ratio = row.idx_tup_fetch / row.idx_tup_read if row.idx_tup_read > 0 else 0
                    
                    index_usage.append({
                        "schema": row.schemaname,
                        "table": row.tablename,
                        "index": row.indexname,
                        "scans": row.idx_scan,
                        "tuples_read": row.idx_tup_read,
                        "tuples_fetched": row.idx_tup_fetch,
                        "usage_ratio": round(usage_ratio, 4),
                        "index_size": row.index_size,
                        "efficiency": "HIGH" if usage_ratio > 0.8 else "MEDIUM" if usage_ratio > 0.5 else "LOW"
                    })
                
                return index_usage
                
        except Exception as e:
            logger.error(f"Error analyzing index usage: {e}")
            return []
    
    async def generate_index_recommendations(self) -> List[IndexRecommendation]:
        """Generate index recommendations based on query patterns"""
        recommendations = []
        
        try:
            # Analyze slow queries for missing indexes
            slow_queries = await self.analyze_query_performance(50)
            
            for query_info in slow_queries:
                query = query_info["query"].lower()
                
                # Look for WHERE clauses that might benefit from indexes
                if "where" in query:
                    # Extract table and column information (simplified)
                    if "portfolio_id" in query and "where" in query:
                        recommendations.append(IndexRecommendation(
                            table_name="portfolios",
                            column_names=["portfolio_id"],
                            index_type="B-tree",
                            reason=f"Frequently queried in slow query: {query_info['mean_time_ms']}ms avg",
                            estimated_benefit="High - reduces table scans",
                            priority=4
                        ))
                    
                    if "optimization_date" in query and "where" in query:
                        recommendations.append(IndexRecommendation(
                            table_name="optimization_results",
                            column_names=["optimization_date"],
                            index_type="B-tree",
                            reason=f"Date filtering in slow query: {query_info['mean_time_ms']}ms avg",
                            estimated_benefit="Medium - improves date range queries",
                            priority=3
                        ))
                
                # Look for JOIN conditions
                if "join" in query:
                    if "asset_id" in query:
                        recommendations.append(IndexRecommendation(
                            table_name="assets",
                            column_names=["asset_id"],
                            index_type="B-tree",
                            reason="JOIN condition in slow query",
                            estimated_benefit="High - improves JOIN performance",
                            priority=5
                        ))
            
            # Remove duplicates and sort by priority
            unique_recommendations = {}
            for rec in recommendations:
                key = (rec.table_name, tuple(rec.column_names))
                if key not in unique_recommendations or unique_recommendations[key].priority < rec.priority:
                    unique_recommendations[key] = rec
            
            return sorted(unique_recommendations.values(), key=lambda x: x.priority, reverse=True)
            
        except Exception as e:
            logger.error(f"Error generating index recommendations: {e}")
            return []
    
    async def analyze_connection_pool_performance(self) -> Dict[str, Any]:
        """Analyze connection pool performance"""
        try:
            async with self.database_manager.get_session() as session:
                # Get connection statistics
                connection_stats_query = text("""
                    SELECT 
                        count(*) as total_connections,
                        count(*) FILTER (WHERE state = 'active') as active_connections,
                        count(*) FILTER (WHERE state = 'idle') as idle_connections,
                        count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction,
                        count(*) FILTER (WHERE state = 'waiting') as waiting_connections,
                        avg(EXTRACT(EPOCH FROM (now() - query_start))) as avg_query_duration_seconds
                    FROM pg_stat_activity 
                    WHERE datname = current_database()
                """)
                
                result = await session.execute(connection_stats_query)
                row = result.fetchone()
                
                # Get database locks
                locks_query = text("""
                    SELECT 
                        count(*) as total_locks,
                        count(*) FILTER (WHERE granted = true) as granted_locks,
                        count(*) FILTER (WHERE granted = false) as waiting_locks
                    FROM pg_locks
                """)
                
                locks_result = await session.execute(locks_query)
                locks_row = locks_result.fetchone()
                
                return {
                    "total_connections": row.total_connections,
                    "active_connections": row.active_connections,
                    "idle_connections": row.idle_connections,
                    "idle_in_transaction": row.idle_in_transaction,
                    "waiting_connections": row.waiting_connections,
                    "avg_query_duration_seconds": round(row.avg_query_duration_seconds or 0, 3),
                    "connection_utilization": round(row.active_connections / max(row.total_connections, 1) * 100, 2),
                    "locks": {
                        "total": locks_row.total_locks,
                        "granted": locks_row.granted_locks,
                        "waiting": locks_row.waiting_locks
                    }
                }
                
        except Exception as e:
            logger.error(f"Error analyzing connection pool performance: {e}")
            return {}
    
    async def generate_optimization_suggestions(self) -> List[OptimizationSuggestion]:
        """Generate comprehensive optimization suggestions"""
        suggestions = []
        
        try:
            # Analyze current performance
            slow_queries = await self.analyze_query_performance(20)
            index_recommendations = await self.generate_index_recommendations()
            connection_stats = await self.analyze_connection_pool_performance()
            
            # Query optimization suggestions
            if slow_queries:
                avg_slow_time = sum(q["mean_time_ms"] for q in slow_queries) / len(slow_queries)
                if avg_slow_time > 500:
                    suggestions.append(OptimizationSuggestion(
                        type="QUERY",
                        title="Optimize Slow Queries",
                        description=f"Average slow query time is {avg_slow_time:.1f}ms. Consider query optimization.",
                        impact="HIGH",
                        effort="MEDIUM",
                        sql_command="-- Review and optimize queries with mean_time > 100ms"
                    ))
            
            # Index suggestions
            high_priority_indexes = [r for r in index_recommendations if r.priority >= 4]
            if high_priority_indexes:
                for rec in high_priority_indexes[:3]:  # Top 3 recommendations
                    suggestions.append(OptimizationSuggestion(
                        type="INDEX",
                        title=f"Create Index on {rec.table_name}.{', '.join(rec.column_names)}",
                        description=f"{rec.reason}. {rec.estimated_benefit}",
                        impact="HIGH",
                        effort="LOW",
                        sql_command=f"CREATE INDEX CONCURRENTLY idx_{rec.table_name}_{'_'.join(rec.column_names)} ON {rec.table_name} ({', '.join(rec.column_names)});"
                    ))
            
            # Connection pool suggestions
            if connection_stats.get("connection_utilization", 0) > 80:
                suggestions.append(OptimizationSuggestion(
                    type="CONFIG",
                    title="Increase Connection Pool Size",
                    description=f"Connection utilization is {connection_stats['connection_utilization']}%. Consider increasing pool size.",
                    impact="MEDIUM",
                    effort="LOW"
                ))
            
            if connection_stats.get("locks", {}).get("waiting", 0) > 5:
                suggestions.append(OptimizationSuggestion(
                    type="QUERY",
                    title="Reduce Lock Contention",
                    description=f"{connection_stats['locks']['waiting']} connections waiting for locks. Optimize transaction patterns.",
                    impact="HIGH",
                    effort="MEDIUM"
                ))
            
            # Database configuration suggestions
            suggestions.append(OptimizationSuggestion(
                type="CONFIG",
                title="Enable Query Plan Caching",
                description="Enable prepared statement caching for frequently executed queries.",
                impact="MEDIUM",
                effort="LOW"
            ))
            
            suggestions.append(OptimizationSuggestion(
                type="CONFIG",
                title="Optimize Shared Buffers",
                description="Review and optimize shared_buffers setting based on available memory.",
                impact="MEDIUM",
                effort="LOW"
            ))
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating optimization suggestions: {e}")
            return []
    
    async def execute_optimization(self, suggestion: OptimizationSuggestion) -> Dict[str, Any]:
        """Execute an optimization suggestion"""
        result = {
            "suggestion_id": f"opt_{datetime.now().timestamp()}",
            "type": suggestion.type,
            "title": suggestion.title,
            "executed_at": datetime.now().isoformat(),
            "success": False,
            "error_message": None,
            "execution_time_ms": 0
        }
        
        start_time = time.time()
        
        try:
            if suggestion.sql_command:
                async with self.database_manager.get_session() as session:
                    await session.execute(text(suggestion.sql_command))
                    await session.commit()
            
            result["success"] = True
            result["execution_time_ms"] = (time.time() - start_time) * 1000
            
            # Record optimization in history
            self.optimization_history.append({
                "timestamp": datetime.now(),
                "suggestion": suggestion,
                "result": result
            })
            
            logger.info(f"Optimization executed successfully: {suggestion.title}")
            
        except Exception as e:
            result["error_message"] = str(e)
            result["execution_time_ms"] = (time.time() - start_time) * 1000
            logger.error(f"Failed to execute optimization: {suggestion.title} - {e}")
        
        return result
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        try:
            # Gather all performance data
            slow_queries = await self.analyze_query_performance(50)
            table_stats = await self.analyze_table_statistics()
            index_usage = await self.analyze_index_usage()
            connection_stats = await self.analyze_connection_pool_performance()
            optimization_suggestions = await self.generate_optimization_suggestions()
            
            # Calculate performance metrics
            total_slow_queries = len(slow_queries)
            avg_slow_query_time = sum(q["mean_time_ms"] for q in slow_queries) / max(total_slow_queries, 1)
            
            # Index efficiency analysis
            efficient_indexes = len([i for i in index_usage if i["efficiency"] == "HIGH"])
            inefficient_indexes = len([i for i in index_usage if i["efficiency"] == "LOW"])
            
            # High priority optimizations
            high_impact_suggestions = [s for s in optimization_suggestions if s.impact == "HIGH"]
            low_effort_suggestions = [s for s in optimization_suggestions if s.effort == "LOW"]
            
            return {
                "report_generated_at": datetime.now().isoformat(),
                "performance_summary": {
                    "total_slow_queries": total_slow_queries,
                    "average_slow_query_time_ms": round(avg_slow_query_time, 2),
                    "connection_utilization_percent": connection_stats.get("connection_utilization", 0),
                    "waiting_locks": connection_stats.get("locks", {}).get("waiting", 0),
                    "efficient_indexes": efficient_indexes,
                    "inefficient_indexes": inefficient_indexes
                },
                "optimization_opportunities": {
                    "total_suggestions": len(optimization_suggestions),
                    "high_impact_suggestions": len(high_impact_suggestions),
                    "low_effort_suggestions": len(low_effort_suggestions),
                    "quick_wins": len([s for s in optimization_suggestions if s.impact in ["HIGH", "MEDIUM"] and s.effort == "LOW"])
                },
                "detailed_analysis": {
                    "slow_queries": slow_queries[:10],  # Top 10 slowest queries
                    "table_statistics": table_stats,
                    "index_usage": index_usage,
                    "connection_statistics": connection_stats
                },
                "recommendations": optimization_suggestions,
                "optimization_history": [
                    {
                        "timestamp": opt["timestamp"].isoformat(),
                        "title": opt["suggestion"].title,
                        "success": opt["result"]["success"]
                    }
                    for opt in self.optimization_history[-10:]  # Last 10 optimizations
                ]
            }
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {"error": str(e)}

# Global optimizer instance
_optimizer: Optional[DatabaseOptimizer] = None

def get_database_optimizer() -> Optional[DatabaseOptimizer]:
    """Get global database optimizer instance"""
    return _optimizer

def initialize_database_optimizer(database_manager):
    """Initialize global database optimizer"""
    global _optimizer
    if _optimizer is None:
        _optimizer = DatabaseOptimizer(database_manager)
        logger.info("Database optimizer initialized")

import time  # Add this import at the top if not already present












