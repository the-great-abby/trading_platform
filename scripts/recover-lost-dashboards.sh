#!/bin/bash

# Recover Lost Grafana Dashboards Script
# This script adds all dashboard JSON files from monitoring/grafana/dashboards/ to the ConfigMap

echo "🏴‍☠️ Recovering lost Grafana dashboards, Captain Abby!"

# Create backup of current ConfigMap
echo "📦 Creating backup of current ConfigMap..."
cp monitoring/grafana-dashboards-configmap.yaml monitoring/grafana-dashboards-configmap.yaml.backup.$(date +%Y%m%d_%H%M%S)

# Get list of dashboards currently in ConfigMap
echo "📋 Current dashboards in ConfigMap:"
grep "\.json: |" monitoring/grafana-dashboards-configmap.yaml | sed 's/  \(.*\)\.json: |/\1/'

# Get list of all dashboard files
echo ""
echo "🗺️ All dashboard files found:"
ls monitoring/grafana/dashboards/*.json | grep -v "dashboard-provider.yaml" | sed 's/.*\///' | sed 's/\.json//'

# Function to check if dashboard exists in ConfigMap
dashboard_exists() {
    local dashboard_name=$1
    grep -q "$dashboard_name.json:" monitoring/grafana-dashboards-configmap.yaml
}

# Function to add dashboard to ConfigMap
add_dashboard_to_configmap() {
    local dashboard_file=$1
    local dashboard_name=$(basename "$dashboard_file" .json)
    
    if dashboard_exists "$dashboard_name"; then
        echo "⚠️  Dashboard $dashboard_name already exists in ConfigMap, skipping..."
        return
    fi
    
    echo "➕ Adding $dashboard_name to ConfigMap..."
    
    # Add dashboard to ConfigMap
    echo "" >> monitoring/grafana-dashboards-configmap.yaml
    echo "  $dashboard_name.json: |" >> monitoring/grafana-dashboards-configmap.yaml
    
    # Add dashboard content with proper indentation
    while IFS= read -r line; do
        echo "    $line" >> monitoring/grafana-dashboards-configmap.yaml
    done < "$dashboard_file"
}

# Add all missing dashboards
echo ""
echo "🔧 Adding missing dashboards to ConfigMap..."

added_count=0
for dashboard_file in monitoring/grafana/dashboards/*.json; do
    if [ -f "$dashboard_file" ]; then
        dashboard_name=$(basename "$dashboard_file" .json)
        
        # Skip the provider file
        if [ "$dashboard_name" = "dashboard-provider" ]; then
            continue
        fi
        
        if ! dashboard_exists "$dashboard_name"; then
            add_dashboard_to_configmap "$dashboard_file"
            ((added_count++))
        fi
    fi
done

echo ""
echo "🎉 Recovery completed!"
echo "📊 Added $added_count new dashboards to ConfigMap"

# Show final dashboard count
echo ""
echo "📋 Final dashboard count:"
grep "\.json: |" monitoring/grafana-dashboards-configmap.yaml | wc -l

echo ""
echo "🔄 To apply the recovered dashboards:"
echo "   kubectl apply -f monitoring/grafana-dashboards-configmap.yaml"
echo "   kubectl rollout restart deployment/grafana -n trading-system"

echo ""
echo "🔗 Access Grafana at: http://localhost:11044 (admin/admin)"


