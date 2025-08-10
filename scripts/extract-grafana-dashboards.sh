#!/bin/bash

# Extract Grafana Dashboards Script
# This script extracts dashboards from ConfigMap files using a more reliable method

echo "🔍 Extracting dashboards from ConfigMap files..."

# Function to extract dashboards from a ConfigMap file
extract_from_configmap() {
    local configmap_file=$1
    local output_dir=$2
    
    if [ ! -f "$configmap_file" ]; then
        echo "⚠️  ConfigMap file not found: $configmap_file"
        return
    fi
    
    echo "📋 Processing $configmap_file..."
    
    # Use sed to extract dashboard sections
    # Look for lines ending with ".json: |" and extract until the next dashboard or end
    local temp_file=$(mktemp)
    
    # Extract dashboard sections
    sed -n '/\.json: |$/,/^[[:space:]]*[a-zA-Z0-9_-]*\.json: |$/p' "$configmap_file" > "$temp_file"
    
    # Process each dashboard section
    local current_dashboard=""
    local in_dashboard=0
    local dashboard_content=""
    
    while IFS= read -r line; do
        # Check if this is a new dashboard start
        if [[ "$line" =~ \.json:\ \|$ ]]; then
            # Save previous dashboard if we have one
            if [ "$in_dashboard" -eq 1 ] && [ -n "$current_dashboard" ] && [ -n "$dashboard_content" ]; then
                echo "$dashboard_content" > "$output_dir/$current_dashboard.json"
                echo "✅ Extracted: $current_dashboard.json"
            fi
            
            # Start new dashboard
            current_dashboard=$(echo "$line" | sed 's/\.json: |$//')
            in_dashboard=1
            dashboard_content=""
        elif [ "$in_dashboard" -eq 1 ]; then
            # Add line to current dashboard content
            dashboard_content="${dashboard_content}${line}"$'\n'
        fi
    done < "$temp_file"
    
    # Save the last dashboard
    if [ "$in_dashboard" -eq 1 ] && [ -n "$current_dashboard" ] && [ -n "$dashboard_content" ]; then
        echo "$dashboard_content" > "$output_dir/$current_dashboard.json"
        echo "✅ Extracted: $current_dashboard.json"
    fi
    
    rm "$temp_file"
}

# Create temporary directory
TEMP_DIR=$(mktemp -d)
echo "📁 Using temporary directory: $TEMP_DIR"

# Extract from all ConfigMap files
extract_from_configmap "k8s/grafana-dashboards-all-fixed.yaml" "$TEMP_DIR"
extract_from_configmap "k8s/grafana-dashboards-restored.yaml" "$TEMP_DIR"
extract_from_configmap "k8s/grafana-dashboards-fixed-v2.yaml" "$TEMP_DIR"
extract_from_configmap "k8s/grafana-dashboards-fixed-v3.yaml" "$TEMP_DIR"

echo ""
echo "📊 Extracted dashboards:"
ls -la "$TEMP_DIR"/*.json 2>/dev/null || echo "No dashboards found"

# Show content of first dashboard as example
if [ -f "$TEMP_DIR"/*.json ]; then
    echo ""
    echo "📄 Example dashboard content:"
    head -20 "$TEMP_DIR"/*.json | head -20
fi

echo ""
echo "🎉 Extraction completed!"
echo "📁 Dashboards extracted to: $TEMP_DIR" 