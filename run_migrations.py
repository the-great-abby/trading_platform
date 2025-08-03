#!/usr/bin/env python3
"""
Script to run database migrations manually
"""
import os
import sys
from alembic import command
from alembic.config import Config

def run_migrations():
    """Run all pending migrations"""
    # Set up alembic config
    alembic_cfg = Config("alembic.ini")
    
    # Set database URL
    os.environ['DATABASE_URL'] = "postgresql://trading_user:trading_pass@postgres-dev:11300/trading_bot"
    
    print("🔧 Running database migrations...")
    
    try:
        # Run upgrade to head
        command.upgrade(alembic_cfg, "head")
        print("✅ Migrations completed successfully!")
        
        # Show current version
        command.current(alembic_cfg)
        
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1) 