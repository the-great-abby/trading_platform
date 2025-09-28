#!/usr/bin/env python3
"""
Environment Variable Loading Examples
====================================

This script demonstrates different ways to load .env files and create environment variables.
"""

import os
import sys
from pathlib import Path

# Method 1: Using python-dotenv (Recommended)
def load_env_with_dotenv():
    """Load .env file using python-dotenv library"""
    try:
        from dotenv import load_dotenv
        
        # Load .env file from current directory
        load_dotenv()
        
        # Or specify a specific path
        # load_dotenv('.env')
        # load_dotenv('/path/to/your/.env')
        
        print("✅ Loaded .env file using python-dotenv")
        return True
    except ImportError:
        print("❌ python-dotenv not installed. Run: pip install python-dotenv")
        return False
    except Exception as e:
        print(f"❌ Error loading .env file: {e}")
        return False

# Method 2: Manual parsing (No dependencies)
def load_env_manually():
    """Manually parse .env file without external dependencies"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Split on first '=' sign
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    # Set environment variable
                    os.environ[key] = value
                    print(f"✅ Set {key} = {value[:10]}{'...' if len(value) > 10 else ''}")
        
        print("✅ Loaded .env file manually")
        return True
    except Exception as e:
        print(f"❌ Error manually loading .env file: {e}")
        return False

# Method 3: Using shell source (Unix/Linux/Mac)
def load_env_with_shell():
    """Load .env file using shell source command"""
    try:
        import subprocess
        
        # Source the .env file and get the environment
        result = subprocess.run(
            ['bash', '-c', 'set -a; source .env; env'],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the output and set environment variables
        for line in result.stdout.split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
        
        print("✅ Loaded .env file using shell source")
        return True
    except Exception as e:
        print(f"❌ Error loading .env with shell: {e}")
        return False

def demonstrate_usage():
    """Demonstrate how to use loaded environment variables"""
    print("\n🔍 Current Environment Variables:")
    print("=" * 50)
    
    # Show some common environment variables
    common_vars = [
        'PUBLIC_API_KEY',
        'DATABASE_URL',
        'REDIS_URL',
        'API_SECRET',
        'DEBUG',
        'PORT'
    ]
    
    for var in common_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'KEY' in var or 'SECRET' in var or 'PASSWORD' in var:
                display_value = value[:8] + '...' if len(value) > 8 else '***'
            else:
                display_value = value
            print(f"  {var} = {display_value}")
        else:
            print(f"  {var} = (not set)")

def create_sample_env():
    """Create a sample .env file for testing"""
    sample_content = """# Sample .env file
# This file contains environment variables for your application

# API Keys
PUBLIC_API_KEY=pk_1234567890abcdef
API_SECRET=your-secret-here

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379

# Application Settings
DEBUG=true
PORT=8080
LOG_LEVEL=INFO

# Trading Configuration
MAX_POSITION_SIZE=0.05
MAX_DAILY_LOSS=1000.0
RISK_LEVEL=MODERATE
"""
    
    with open('.env.sample', 'w') as f:
        f.write(sample_content)
    
    print("✅ Created .env.sample file")

def main():
    """Main function to demonstrate all methods"""
    print("🔧 Environment Variable Loading Examples")
    print("=" * 50)
    
    # Create sample .env file
    create_sample_env()
    
    print("\n1️⃣ Method 1: Using python-dotenv (Recommended)")
    print("-" * 50)
    if load_env_with_dotenv():
        demonstrate_usage()
    
    print("\n2️⃣ Method 2: Manual parsing")
    print("-" * 50)
    # Copy sample to .env for testing
    import shutil
    shutil.copy('.env.sample', '.env')
    
    if load_env_manually():
        demonstrate_usage()
    
    print("\n3️⃣ Method 3: Using shell source")
    print("-" * 50)
    if load_env_with_shell():
        demonstrate_usage()
    
    print("\n📚 Best Practices:")
    print("-" * 50)
    print("✅ Use python-dotenv for Python applications")
    print("✅ Add .env to .gitignore to keep secrets safe")
    print("✅ Use .env.example for documentation")
    print("✅ Validate required environment variables")
    print("✅ Use type conversion for non-string values")
    
    # Cleanup
    if os.path.exists('.env.sample'):
        os.remove('.env.sample')
    if os.path.exists('.env'):
        os.remove('.env')

if __name__ == "__main__":
    main()


