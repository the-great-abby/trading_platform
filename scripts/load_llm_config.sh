#!/bin/bash
# Load LLM Configuration from .env file
# Source this in your shell profile or run before starting services

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if .env file exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo "✅ Loading LLM configuration from .env"
    
    # Export variables from .env file
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
    
    echo "📋 LLM Provider: ${LLM_PROVIDER:-not set}"
    echo "📋 LM Studio URL: ${LMSTUDIO_BASE_URL:-not set}"
    echo "📋 Ollama URL: ${OLLAMA_BASE_URL:-not set}"
else
    echo "⚠️  No .env file found. Copy .env.example to .env and customize."
    echo "   cp $PROJECT_ROOT/.env.example $PROJECT_ROOT/.env"
fi








