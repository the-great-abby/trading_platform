#!/bin/bash

# Fix Registry URLs Script
# Updates Docker build/push commands from localhost:5000 to localhost:32000
# Note: Kubernetes YAML files should keep localhost:5000 for internal cluster access

echo "🔧 Fixing registry URLs for Docker build/push commands..."

# Find Makefiles and scripts with localhost:5000
FILES_TO_UPDATE=$(grep -l "localhost:5000" Makefile* scripts/*.sh 2>/dev/null || true)

if [ -z "$FILES_TO_UPDATE" ]; then
    echo "✅ No files found with localhost:5000 references"
    exit 0
fi

echo "📁 Found $(echo "$FILES_TO_UPDATE" | wc -l) files to update:"
echo "$FILES_TO_UPDATE" | sed 's/^/  - /'

# Create backup
BACKUP_DIR="backup/registry-fix-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "💾 Creating backup in $BACKUP_DIR..."

# Update each file
for file in $FILES_TO_UPDATE; do
    echo "🔄 Updating $file..."
    
    # Create backup
    cp "$file" "$BACKUP_DIR/"
    
    # Update the file (only Docker build/push commands)
    sed -i.bak 's/docker build -t localhost:5000/docker build -t localhost:32000/g' "$file"
    sed -i.bak 's/docker push localhost:5000/docker push localhost:32000/g' "$file"
    sed -i.bak 's/REGISTRY_URL := localhost:5000/REGISTRY_URL := localhost:32000/g' "$file"
    
    # Remove backup file created by sed
    rm -f "$file.bak"
    
    echo "✅ Updated $file"
done

echo ""
echo "🎉 Registry URL fix completed!"
echo "📊 Summary:"
echo "  - Files updated: $(echo "$FILES_TO_UPDATE" | wc -l)"
echo "  - Backup location: $BACKUP_DIR"
echo ""
echo "⚠️  Note: Kubernetes YAML files still use localhost:5000 for internal cluster access"
echo "   This fix only updates Docker build/push commands for local development"
echo ""
echo "🔍 To verify the fix, run:"
echo "  grep -r 'localhost:32000' Makefile* scripts/*.sh | head -5" 