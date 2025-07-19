#!/usr/bin/env python3
"""
CLI utility to manage and analyze database indexes using DatabaseOptimizer
"""
import sys
import asyncio
from src.utils.database_optimizer import DatabaseOptimizer

DB_URL = 'postgresql://trading_user:trading_pass@postgres-dev:5432/trading_bot'

async def main():
    if len(sys.argv) < 2:
        print("Usage: manage_indexes.py [ensure|analyze|report]")
        sys.exit(1)
    command = sys.argv[1]
    optimizer = DatabaseOptimizer(DB_URL)
    if command == 'ensure':
        print("🔧 Ensuring all required indexes...")
        await optimizer.ensure_indexes()
        print("✅ Index creation complete.")
    elif command == 'analyze':
        print("🔍 Analyzing for missing indexes...")
        missing = await optimizer.find_missing_indexes()
        if not missing:
            print("✅ No missing indexes detected.")
        else:
            print(f"⚠️  {len(missing)} missing indexes found:")
            for idx in missing:
                print(f"  - {idx.table_name}.{idx.column_name} ({idx.reason})")
    elif command == 'report':
        print("📊 Generating performance report...")
        report = await optimizer.get_performance_report()
        for k, v in report.items():
            print(f"{k}: {v}")
    else:
        print("Unknown command. Use: ensure, analyze, or report.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 