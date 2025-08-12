#!/bin/bash

# Add Dashboards Properly Script
# This script adds dashboard JSON files to the ConfigMap with proper YAML formatting

echo "🏴‍☠️ Adding dashboards properly, Captain Abby!"

# List of important dashboards to add (excluding test files)
IMPORTANT_DASHBOARDS=(
    "trading-engine"
    "order-execution"
    "backtest-performance"
    "risk-management-enhanced"
    "llm-proxy-dashboard"
    "database-performance-dashboard"
    "message-queue-health-dashboard"
    "infrastructure-monitoring"
    "rabbitmq-monitoring"
    "ai-performance-fixed"
    "strategy-performance-fixed"
    "system-infrastructure-fixed"
    "market-data-dashboard-fixed"
    "backtest-performance-dashboard-fixed"
    "risk-management-enhanced-fixed"
)

# Function to check if dashboard exists in ConfigMap
dashboard_exists() {
    local dashboard_name=$1
    grep -q "$dashboard_name.json:" monitoring/grafana-dashboards-configmap.yaml
}

# Function to add dashboard to ConfigMap with proper formatting
add_dashboard_to_configmap() {
    local dashboard_file=$1
    local dashboard_name=$(basename "$dashboard_file" .json)
    
    if dashboard_exists "$dashboard_name"; then
        echo "⚠️  Dashboard $dashboard_name already exists in ConfigMap, skipping..."
        return
    fi
    
    echo "➕ Adding $dashboard_name to ConfigMap..."
    
    # Add dashboard to ConfigMap with proper YAML formatting
    echo "" >> monitoring/grafana-dashboards-configmap.yaml
    echo "  $dashboard_name.json: |" >> monitoring/grafana-dashboards-configmap.yaml
    
    # Add dashboard content with proper indentation (4 spaces)
    while IFS= read -r line; do
        echo "    $line" >> monitoring/grafana-dashboards-configmap.yaml
    done < "$dashboard_file"
}

# Add important dashboards
echo ""
echo "🔧 Adding important dashboards to ConfigMap..."

added_count=0
for dashboard in "${IMPORTANT_DASHBOARDS[@]}"; do
    dashboard_file="monitoring/grafana/dashboards/$dashboard.json"
    if [ -f "$dashboard_file" ]; then
        add_dashboard_to_configmap "$dashboard_file"
        ((added_count++))
    else
        echo "⚠️  Dashboard file not found: $dashboard_file"
    fi
done

echo ""
echo "🎉 Dashboard addition completed!"
echo "📊 Added $added_count new dashboards to ConfigMap"

# Show final dashboard count
echo ""
echo "📋 Final dashboard count:"
grep "\.json: |" monitoring/grafana-dashboards-configmap.yaml | wc -l

echo ""
echo "🔄 To apply the dashboards:"
echo "   kubectl apply -f monitoring/grafana-dashboards-configmap.yaml"
echo "   kubectl rollout restart deployment/grafana -n trading-system"

echo ""
echo "🔗 Access Grafana at: http://localhost:11044 (admin/admin)"





