#!/bin/bash

# Script to update all Kubernetes YAML files to use the correct registry
# Changes localhost:5000 to localhost:32000 to avoid iTunes conflicts

echo "🔄 Updating registry configuration across all Kubernetes files..."
echo "📝 Changing localhost:5000 to localhost:32000"

# Find all YAML files in k8s directory that contain localhost:5000
files_to_update=$(find k8s -name "*.yaml" -exec grep -l "localhost:5000" {} \;)

# Count total files
total_files=$(echo "$files_to_update" | wc -l)
echo "📊 Found $total_files files to update"

# Update each file
updated_count=0
for file in $files_to_update; do
    if [ -f "$file" ]; then
        echo "🔄 Updating: $file"
        sed -i '' 's/localhost:5000/localhost:32000/g' "$file"
        updated_count=$((updated_count + 1))
    fi
done

echo "✅ Updated $updated_count files"
echo "🎯 Registry configuration updated to use localhost:32000"

# Show a summary of what was changed
echo ""
echo "📋 Summary of changes:"
echo "   - Changed localhost:5000 → localhost:32000"
echo "   - Updated $updated_count Kubernetes YAML files"
echo "   - Registry now uses port 32000 (avoiding iTunes conflict)"
echo ""
echo "💡 Next steps:"
echo "   1. Rebuild any custom images: docker build -t localhost:32000/<service>:latest ."
echo "   2. Push images to new registry: docker push localhost:32000/<service>:latest"
echo "   3. Apply updated configurations: kubectl apply -f k8s/<service>.yaml" 