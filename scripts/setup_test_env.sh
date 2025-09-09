#!/bin/bash
"""
Setup script for test virtual environment
Creates and configures the test environment with all necessary dependencies
"""

set -e

echo "🐍 Setting up test virtual environment..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_ENV_PATH="$PROJECT_ROOT/test-env"

# Check if test environment exists
if [ ! -d "$TEST_ENV_PATH" ]; then
    echo "❌ Test environment not found. Creating..."
    python3 -m venv "$TEST_ENV_PATH"
    echo "✅ Test environment created at $TEST_ENV_PATH"
else
    echo "✅ Test environment already exists at $TEST_ENV_PATH"
fi

# Activate test environment
echo "🔄 Activating test environment..."
source "$TEST_ENV_PATH/bin/activate"

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install base dependencies
echo "📦 Installing base dependencies..."
pip install -r requirements.txt

# Install test-specific dependencies
echo "🧪 Installing test dependencies..."
pip install pytest pytest-asyncio pytest-cov pytest-html pytest-mock
pip install asyncpg redis aio-pika
pip install coverage pytest-xdist

# Install development dependencies
echo "🔧 Installing development dependencies..."
pip install black flake8 mypy
pip install pre-commit

# Verify installation
echo "✅ Verifying installation..."
python -c "import pytest; print(f'pytest version: {pytest.__version__}')"
python -c "import asyncpg; print('asyncpg installed')"
python -c "import redis; print('redis installed')"
python -c "import aio_pika; print('aio-pika installed')"

echo "🎉 Test environment setup complete!"
echo ""
echo "To activate the test environment:"
echo "  source test-env/bin/activate"
echo ""
echo "To run tests:"
echo "  python scripts/run_cqrs_tests.py"
echo ""
echo "To deactivate:"
echo "  deactivate"
