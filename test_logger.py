#!/usr/bin/env python3

def test_startup_event():
    """Test the startup event function"""
    import logging
    
    async def startup_event():
        """Initialize application on startup"""
        import logging
        logger = logging.getLogger("cqrs_api")
        logger.info("Starting CQRS API application")
        
        # Initialize database connection
        import os
        from src.services.database import initialize_database
        
        database_url = os.getenv("DATABASE_URL", "postgresql://trading_user:trading_pass@timescaledb.trading-system.svc.cluster.local:5432/trading_bot")
        
        try:
            db_manager = await initialize_database(database_url)
            print("Database connection successful")
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
    
    # Test the function
    import asyncio
    result = asyncio.run(startup_event())
    print(f"Test result: {result}")

if __name__ == "__main__":
    test_startup_event()
