#!/bin/bash

# Setup script for Kubernetes Job Generator
# This script creates and configures the virtual environment for the job generator

set -e

echo "=== Setting up Kubernetes Job Generator Environment ==="

# Check if virtual environment already exists
if [ -d "k8s-job-generator-env" ]; then
    echo "Virtual environment already exists. Updating dependencies..."
else
    echo "Creating virtual environment..."
    python3 -m venv k8s-job-generator-env
fi

# Activate virtual environment
echo "Activating virtual environment..."
source k8s-job-generator-env/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install pyyaml

# Test the installation
echo "Testing job generator..."
python3 scripts/generate_k8s_job.py --type backtest --script test_backtest.py --help > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Job generator setup successful!"
    echo ""
    echo "=== Usage Examples ==="
    echo "Basic backtest:"
    echo "  make k8s-job-backtest SCRIPT=run_backtest.py"
    echo ""
    echo "LLM-enhanced backtest:"
    echo "  make k8s-job-backtest SCRIPT=run_llm_evaluated_backtest.py USE_LLM=true"
    echo ""
    echo "Custom parameters:"
    echo "  make k8s-job-backtest SCRIPT=run_backtest.py SYMBOLS=AAPL,TSLA,MSFT START_DATE=2024-01-01 END_DATE=2024-01-31"
    echo ""
    echo "Apply directly to Kubernetes:"
    echo "  make k8s-job-backtest SCRIPT=run_backtest.py APPLY=true"
    echo ""
    echo "=== Virtual Environment ==="
    echo "To activate manually: source k8s-job-generator-env/bin/activate"
    echo "To deactivate: deactivate"
else
    echo "❌ Job generator setup failed!"
    exit 1
fi 