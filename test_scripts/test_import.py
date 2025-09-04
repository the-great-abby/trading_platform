#!/usr/bin/env python3
"""
Test import and class inspection
"""

import os
import sys
sys.path.append('src')

def test_import():
    """Test import and inspect the class"""
    
    print("🔍 Testing Import and Class Inspection")
    print("=" * 40)
    
    try:
        from src.services.database.market_data_service import MarketDataDatabaseService
        print("✅ Import successful")
        
        # Inspect the class
        print(f"📋 Class name: {MarketDataDatabaseService.__name__}")
        print(f"📋 Class module: {MarketDataDatabaseService.__module__}")
        
        # List all methods
        methods = [method for method in dir(MarketDataDatabaseService) if not method.startswith('_')]
        print(f"📋 Available methods: {methods}")
        
        # Check if get_all_symbols exists
        if 'get_all_symbols' in methods:
            print("✅ get_all_symbols method found")
        else:
            print("❌ get_all_symbols method NOT found")
        
        # Try to create an instance
        db_url = os.getenv('DATABASE_URL', 'postgresql://trading_user:trading_pass@postgres-dev:5432/trading_bot')
        service = MarketDataDatabaseService(db_url)
        print("✅ Service instance created")
        
        # List instance methods
        instance_methods = [method for method in dir(service) if not method.startswith('_')]
        print(f"📋 Instance methods: {instance_methods}")
        
        if 'get_all_symbols' in instance_methods:
            print("✅ get_all_symbols method found in instance")
        else:
            print("❌ get_all_symbols method NOT found in instance")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_import() 