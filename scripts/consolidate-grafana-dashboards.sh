#!/bin/bash

# Consolidate Grafana Dashboards Script
# This script extracts useful dashboards from conflicting ConfigMaps and consolidates them into the primary one

echo "🔄 Consolidating Grafana dashboards..."

# Create backup of current primary ConfigMap
echo "📦 Creating backup of current primary ConfigMap..."
cp monitoring/grafana-dashboards-configmap.yaml monitoring/grafana-dashboards-configmap.yaml.backup.$(date +%Y%m%d_%H%M%S)

# Function to extract dashboards from a ConfigMap file
extract_dashboards() {
    local configmap_file=$1
    local output_dir=$2
    
    if [ ! -f "$configmap_file" ]; then
        echo "⚠️  ConfigMap file not found: $configmap_file"
        return
    fi
    
    echo "📋 Extracting dashboards from $configmap_file..."
    
    # Extract dashboard JSON files from ConfigMap
    # Look for patterns like "dashboard-name.json: |" and extract the content
    awk '
    /\.json: \|$/ {
        # Extract dashboard name
        dashboard_name = $1
        gsub(/\.json: \|$/, "", dashboard_name)
        
        # Start collecting content
        in_dashboard = 1
        dashboard_content = ""
        next
    }
    
    in_dashboard && /^[[:space:]]*[^[:space:]]/ && !/^[[:space:]]*[a-zA-Z0-9_-]+\.json: \|$/ {
        # End of dashboard content
        in_dashboard = 0
        
        # Save dashboard content
        if (dashboard_name != "" && dashboard_content != "") {
            output_file = "'$output_dir'/" dashboard_name ".json"
            print dashboard_content > output_file
            print "✅ Extracted: " dashboard_name ".json"
        }
    }
    
    in_dashboard {
        # Collect dashboard content (remove leading spaces)
        gsub(/^[[:space:]]*/, "")
        if ($0 != "") {
            dashboard_content = dashboard_content $0 "\n"
        }
    }
    ' "$configmap_file"
}

# Create temporary directory for extracted dashboards
TEMP_DIR=$(mktemp -d)
echo "📁 Using temporary directory: $TEMP_DIR"

# Extract dashboards from conflicting ConfigMaps
echo ""
echo "🔍 Extracting dashboards from conflicting ConfigMaps..."

extract_dashboards "k8s/grafana-dashboards-all-fixed.yaml" "$TEMP_DIR"
extract_dashboards "k8s/grafana-dashboards-restored.yaml" "$TEMP_DIR"
extract_dashboards "k8s/grafana-dashboards-fixed-v2.yaml" "$TEMP_DIR"
extract_dashboards "k8s/grafana-dashboards-fixed-v3.yaml" "$TEMP_DIR"

# List extracted dashboards
echo ""
echo "📊 Extracted dashboards:"
ls -la "$TEMP_DIR"/*.json 2>/dev/null || echo "No dashboards found"

# Function to check if dashboard already exists in primary ConfigMap
dashboard_exists() {
    local dashboard_name=$1
    grep -q "$dashboard_name.json:" monitoring/grafana-dashboards-configmap.yaml
}

# Function to add dashboard to primary ConfigMap
add_dashboard_to_configmap() {
    local dashboard_file=$1
    local dashboard_name=$(basename "$dashboard_file" .json)
    
    # Check if file has content
    if [ ! -s "$dashboard_file" ]; then
        echo "⚠️  Dashboard $dashboard_name has no content, skipping..."
        return
    fi
    
    if dashboard_exists "$dashboard_name"; then
        echo "⚠️  Dashboard $dashboard_name already exists in primary ConfigMap, skipping..."
        return
    fi
    
    echo "➕ Adding $dashboard_name to primary ConfigMap..."
    
    # Add dashboard to ConfigMap
    echo "" >> monitoring/grafana-dashboards-configmap.yaml
    echo "  $dashboard_name.json: |" >> monitoring/grafana-dashboards-configmap.yaml
    
    # Add dashboard content with proper indentation
    while IFS= read -r line; do
        echo "    $line" >> monitoring/grafana-dashboards-configmap.yaml
    done < "$dashboard_file"
}

# Add extracted dashboards to primary ConfigMap
echo ""
echo "🔧 Adding dashboards to primary ConfigMap..."

for dashboard_file in "$TEMP_DIR"/*.json; do
    if [ -f "$dashboard_file" ]; then
        add_dashboard_to_configmap "$dashboard_file"
    fi
done

# Clean up temporary directory
rm -rf "$TEMP_DIR"

echo ""
echo "📋 Current dashboards in primary ConfigMap:"
grep "\.json: |" monitoring/grafana-dashboards-configmap.yaml | sed 's/^[[:space:]]*//' | sed 's/\.json: |$//' | sort

echo ""
echo "🎉 Dashboard consolidation completed!"
echo "📦 Primary ConfigMap updated: monitoring/grafana-dashboards-configmap.yaml"
echo ""
echo "🔄 To apply the consolidated ConfigMap:"
echo "   kubectl apply -f monitoring/grafana-dashboards-configmap.yaml"
echo "   kubectl rollout restart deployment/grafana -n trading-system"
echo ""
echo "🔗 Access Grafana at: http://localhost:11044 (admin/admin)" 