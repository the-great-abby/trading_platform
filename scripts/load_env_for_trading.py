#!/usr/bin/env python3
"""
Load Environment Variables for Trading Service
============================================

This script demonstrates how to load .env files for the trading service
and provides utilities for environment variable management.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

def load_trading_env(env_file: str = '.env') -> bool:
    """
    Load environment variables from .env file for trading service
    
    Args:
        env_file: Path to .env file (default: '.env')
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from dotenv import load_dotenv
        
        # Load .env file
        env_path = Path(env_file)
        if not env_path.exists():
            print(f"❌ .env file not found: {env_path.absolute()}")
            return False
        
        # Load environment variables
        load_dotenv(env_path)
        print(f"✅ Loaded environment variables from {env_path.absolute()}")
        return True
        
    except ImportError:
        print("❌ python-dotenv not installed. Run: pip install python-dotenv")
        return False
    except Exception as e:
        print(f"❌ Error loading .env file: {e}")
        return False

def validate_trading_env() -> Dict[str, Any]:
    """
    Validate required environment variables for trading service
    
    Returns:
        Dict containing validation results
    """
    required_vars = {
        'PUBLIC_API_SECRET': 'Public.com API secret key',
        'DATABASE_URL': 'Database connection string',
        'REDIS_URL': 'Redis connection string'
    }
    
    optional_vars = {
        'PUBLIC_API_TIMEOUT': 'API timeout in seconds',
        'PUBLIC_API_MAX_RETRIES': 'Maximum API retries',
        'PUBLIC_API_RATE_LIMIT': 'API rate limit',
        'PUBLIC_API_RATE_LIMIT_WINDOW': 'Rate limit window in seconds',
        'LOG_LEVEL': 'Logging level',
        'DEBUG': 'Debug mode'
    }
    
    results = {
        'required': {},
        'optional': {},
        'missing_required': [],
        'all_valid': True
    }
    
    # Check required variables
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            results['required'][var] = {
                'value': value[:10] + '...' if len(value) > 10 else value,
                'description': description,
                'present': True
            }
        else:
            results['missing_required'].append(var)
            results['all_valid'] = False
    
    # Check optional variables
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            results['optional'][var] = {
                'value': value,
                'description': description,
                'present': True
            }
        else:
            results['optional'][var] = {
                'value': None,
                'description': description,
                'present': False
            }
    
    return results

def print_env_status():
    """Print current environment variable status"""
    print("🔍 Trading Service Environment Variables")
    print("=" * 50)
    
    validation = validate_trading_env()
    
    # Required variables
    print("\n📋 Required Variables:")
    print("-" * 30)
    for var, info in validation['required'].items():
        status = "✅" if info['present'] else "❌"
        print(f"  {status} {var}: {info['value']}")
        print(f"      {info['description']}")
    
    # Missing required variables
    if validation['missing_required']:
        print(f"\n❌ Missing Required Variables:")
        for var in validation['missing_required']:
            print(f"  - {var}")
    
    # Optional variables
    print("\n📋 Optional Variables:")
    print("-" * 30)
    for var, info in validation['optional'].items():
        status = "✅" if info['present'] else "⚪"
        value = info['value'] if info['present'] else "(not set)"
        print(f"  {status} {var}: {value}")
        print(f"      {info['description']}")
    
    # Overall status
    print(f"\n🎯 Overall Status:")
    if validation['all_valid']:
        print("  ✅ All required environment variables are set!")
    else:
        print("  ❌ Some required environment variables are missing.")
        print("  💡 Create a .env file with the missing variables.")

def create_trading_env_template():
    """Create a template .env file for trading service"""
    template_content = """# Trading Service Environment Variables
# Copy this file to .env and fill in your actual values

# Public.com API Configuration
PUBLIC_API_SECRET=sk_your_public_api_secret_here
PUBLIC_API_TIMEOUT=30
PUBLIC_API_MAX_RETRIES=3
PUBLIC_API_RATE_LIMIT=100
PUBLIC_API_RATE_LIMIT_WINDOW=60

# Database Configuration
DATABASE_URL=postgresql+asyncpg://trading_user:trading_pass@timescaledb.trading-system.svc.cluster.local:5432/trading_bot
REDIS_URL=redis://redis.trading-system.svc.cluster.local:6379

# Application Configuration
LOG_LEVEL=INFO
DEBUG=false
PORT=8080

# Trading Configuration
MAX_POSITION_SIZE=0.05
MAX_DAILY_LOSS=1000.0
RISK_LEVEL=MODERATE
MAX_DAILY_TRADES=15

# Elliott Wave Service (Optional)
ELLIOTT_WAVE_SERVICE_URL=http://elliott-wave-service.trading-system.svc.cluster.local:8000
ELLIOTT_WAVE_CONFIDENCE_THRESHOLD=0.6

# Monitoring (Optional)
ENABLE_METRICS=true
METRICS_PORT=9090
"""
    
    template_file = Path('.env.template')
    with open(template_file, 'w') as f:
        f.write(template_content)
    
    print(f"✅ Created .env template: {template_file.absolute()}")
    print("💡 Copy this to .env and fill in your actual values")

def load_and_validate():
    """Load .env file and validate environment variables"""
    print("🔧 Loading Trading Service Environment Variables")
    print("=" * 50)
    
    # Load .env file
    if not load_trading_env():
        print("\n💡 Creating .env template...")
        create_trading_env_template()
        return False
    
    # Validate environment variables
    print("\n🔍 Validating environment variables...")
    print_env_status()
    
    validation = validate_trading_env()
    return validation['all_valid']

def main():
    """Main function"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'load':
            load_trading_env()
        elif command == 'validate':
            print_env_status()
        elif command == 'template':
            create_trading_env_template()
        elif command == 'check':
            load_and_validate()
        else:
            print("❌ Unknown command. Use: load, validate, template, or check")
    else:
        # Default: load and validate
        success = load_and_validate()
        if success:
            print("\n🎉 Environment is ready for trading!")
        else:
            print("\n⚠️ Please fix the environment configuration before proceeding.")

if __name__ == "__main__":
    main()
