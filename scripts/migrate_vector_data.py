#!/usr/bin/env python3
"""
Vector Data Migration Script
Migrates vector embeddings from TimescaleDB to dedicated PostgreSQL databases
"""

import psycopg2
import json
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configurations
SOURCE_DB = {
    'host': 'timescaledb.trading-system.svc.cluster.local',
    'port': 5432,
    'database': 'trading_bot',
    'user': 'trading_user',
    'password': 'trading_pass'
}

K8S_DB = {
    'host': 'postgres-vector.postgres-infra.svc.cluster.local',
    'port': 5432,
    'database': 'kubernetes_vector_db',
    'user': 'postgres',
    'password': 'postgres'
}

FINANCIAL_DB = {
    'host': 'postgres-vector.postgres-infra.svc.cluster.local',
    'port': 5432,
    'database': 'financial_vector_db',
    'user': 'postgres',
    'password': 'postgres'
}

def get_connection(db_config: Dict[str, Any]):
    """Create database connection"""
    try:
        conn = psycopg2.connect(**db_config)
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to {db_config['database']}: {e}")
        return None

def migrate_vector_data():
    """Migrate vector data to new databases"""
    
    # Connect to source database
    source_conn = get_connection(SOURCE_DB)
    if not source_conn:
        logger.error("Failed to connect to source database")
        return
    
    # Connect to destination databases
    k8s_conn = get_connection(K8S_DB)
    financial_conn = get_connection(FINANCIAL_DB)
    
    if not k8s_conn or not financial_conn:
        logger.error("Failed to connect to destination databases")
        source_conn.close()
        return
    
    try:
        # Get vector types and counts
        with source_conn.cursor() as cursor:
            cursor.execute("""
                SELECT vector_type, COUNT(*) 
                FROM vector_embeddings 
                GROUP BY vector_type
                ORDER BY vector_type
            """)
            vector_types = cursor.fetchall()
            logger.info(f"Found vector types: {vector_types}")
        
        # Migrate Kubernetes data
        k8s_types = ['architecture_kubernetes', 'architecture_monitoring']
        logger.info("Migrating Kubernetes data...")
        
        with source_conn.cursor() as source_cursor:
            for vector_type in k8s_types:
                source_cursor.execute("""
                    SELECT id, content, embedding, meta_info, vector_type, created_at, updated_at
                    FROM vector_embeddings 
                    WHERE vector_type = %s
                """, (vector_type,))
                
                records = source_cursor.fetchall()
                logger.info(f"Found {len(records)} records for {vector_type}")
                
                if records:
                    with k8s_conn.cursor() as dest_cursor:
                        for record in records:
                            # Handle JSONB data properly
                            id_val, content, embedding, meta_info, vector_type_val, created_at, updated_at = record
                            
                            # Convert meta_info to JSON string if it's a dict
                            if isinstance(meta_info, dict):
                                meta_info_json = json.dumps(meta_info)
                            else:
                                meta_info_json = meta_info
                            
                            dest_cursor.execute("""
                                INSERT INTO vector_embeddings 
                                (id, content, embedding, meta_info, vector_type, created_at, updated_at)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (id) DO UPDATE SET
                                content = EXCLUDED.content,
                                embedding = EXCLUDED.embedding,
                                meta_info = EXCLUDED.meta_info,
                                updated_at = CURRENT_TIMESTAMP
                            """, (id_val, content, embedding, meta_info_json, vector_type_val, created_at, updated_at))
                    
                    k8s_conn.commit()
                    logger.info(f"Migrated {len(records)} records for {vector_type}")
        
        # Migrate Financial data
        financial_types = ['architecture_trading', 'architecture_api', 'architecture_database', 'architecture_general']
        logger.info("Migrating Financial data...")
        
        with source_conn.cursor() as source_cursor:
            for vector_type in financial_types:
                source_cursor.execute("""
                    SELECT id, content, embedding, meta_info, vector_type, created_at, updated_at
                    FROM vector_embeddings 
                    WHERE vector_type = %s
                """, (vector_type,))
                
                records = source_cursor.fetchall()
                logger.info(f"Found {len(records)} records for {vector_type}")
                
                if records:
                    with financial_conn.cursor() as dest_cursor:
                        for record in records:
                            # Handle JSONB data properly
                            id_val, content, embedding, meta_info, vector_type_val, created_at, updated_at = record
                            
                            # Convert meta_info to JSON string if it's a dict
                            if isinstance(meta_info, dict):
                                meta_info_json = json.dumps(meta_info)
                            else:
                                meta_info_json = meta_info
                            
                            dest_cursor.execute("""
                                INSERT INTO vector_embeddings 
                                (id, content, embedding, meta_info, vector_type, created_at, updated_at)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (id) DO UPDATE SET
                                content = EXCLUDED.content,
                                embedding = EXCLUDED.embedding,
                                meta_info = EXCLUDED.meta_info,
                                updated_at = CURRENT_TIMESTAMP
                            """, (id_val, content, embedding, meta_info_json, vector_type_val, created_at, updated_at))
                    
                    financial_conn.commit()
                    logger.info(f"Migrated {len(records)} records for {vector_type}")
        
        # Verify migration
        logger.info("Verifying migration...")
        
        with k8s_conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM vector_embeddings")
            k8s_count = cursor.fetchone()[0]
            logger.info(f"Kubernetes database: {k8s_count} records")
        
        with financial_conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM vector_embeddings")
            financial_count = cursor.fetchone()[0]
            logger.info(f"Financial database: {financial_count} records")
        
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        source_conn.rollback()
        k8s_conn.rollback()
        financial_conn.rollback()
    finally:
        source_conn.close()
        k8s_conn.close()
        financial_conn.close()

if __name__ == "__main__":
    migrate_vector_data()
