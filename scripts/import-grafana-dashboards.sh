#!/bin/bash

# Import Grafana Dashboards Script
# This script imports all dashboard JSON files from the monitoring/grafana/dashboards directory

echo "🔄 Importing Grafana Dashboards..."

# Check if Grafana is accessible
if ! curl -s -f http://localhost:11044/api/health > /dev/null; then
    echo "❌ Grafana is not accessible. Please ensure Grafana is running and port forwarding is active."
    echo "   Run: kubectl port-forward -n trading-system svc/grafana 11044:3000"
    exit 1
fi

# Import all JSON dashboard files (excluding the provider file)
for dashboard_file in monitoring/grafana/dashboards/*.json; do
    if [ -f "$dashboard_file" ]; then
        dashboard_name=$(basename "$dashboard_file" .json)
        echo "📊 Importing $dashboard_name..."
        
        response=$(curl -s -X POST \
            -H "Content-Type: application/json" \
            -u admin:admin \
            -d @"$dashboard_file" \
            http://localhost:11044/api/dashboards/db)
        
        if echo "$response" | jq -e '.status' > /dev/null 2>&1; then
            status=$(echo "$response" | jq -r '.status')
            if [ "$status" = "success" ]; then
                echo "✅ Successfully imported $dashboard_name"
            else
                echo "⚠️  Imported $dashboard_name with status: $status"
            fi
        else
            echo "❌ Failed to import $dashboard_name"
        fi
    fi
done

echo ""
echo "🎉 Dashboard import completed!"
echo "📊 Access Grafana at: http://localhost:11044"
echo "👤 Login with: admin/admin"
echo ""
echo "Available dashboards:"
curl -s -u admin:admin http://localhost:11044/api/search | jq -r '.[].title' | sed 's/^/  • /' 