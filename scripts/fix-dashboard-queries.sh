#!/bin/bash

# Fix Dashboard Queries Script
# This script identifies missing metrics and suggests fixes

echo "🔍 Analyzing available metrics vs dashboard queries..."

# Check for missing metrics that dashboards commonly use
echo ""
echo "📊 Checking for commonly used metrics:"

# Trading metrics
echo "Trading Metrics:"
curl -s "http://localhost:11045/api/v1/query?query=trading_trades_total" | jq -r '.data.result | length' | xargs echo "  • trading_trades_total: $1 results"
curl -s "http://localhost:11045/api/v1/query?query=trading_winning_trades_total" | jq -r '.data.result | length' | xargs echo "  • trading_winning_trades_total: $1 results"
curl -s "http://localhost:11045/api/v1/query?query=trading_requests_total" | jq -r '.data.result | length' | xargs echo "  • trading_requests_total: $1 results"

# System metrics
echo ""
echo "System Metrics:"
curl -s "http://localhost:11045/api/v1/query?query=node_cpu_seconds_total" | jq -r '.data.result | length' | xargs echo "  • node_cpu_seconds_total: $1 results"
curl -s "http://localhost:11045/api/v1/query?query=node_memory_MemAvailable_bytes" | jq -r '.data.result | length' | xargs echo "  • node_memory_MemAvailable_bytes: $1 results"
curl -s "http://localhost:11045/api/v1/query?query=node_filesystem_avail_bytes" | jq -r '.data.result | length' | xargs echo "  • node_filesystem_avail_bytes: $1 results"

echo ""
echo "💡 Recommendations:"
echo "1. Use 'trading_requests_total' instead of 'trading_trades_total'"
echo "2. Use 'trading_pnl_total' for P&L metrics"
echo "3. Use 'trading_active_positions' for position counts"
echo "4. System metrics are now available via Node Exporter"
echo ""
echo "📊 Check the 'Metrics Diagnostic' dashboard to see all available metrics"
echo "🔧 Use the 'System Infrastructure (Complete)' dashboard for full system monitoring" 