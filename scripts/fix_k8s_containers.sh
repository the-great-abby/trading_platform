#!/bin/bash

echo "🔧 Fixing Kubernetes Container Issues..."

# Function to add imagePullPolicy: Never to a deployment
add_image_pull_policy() {
    local file=$1
    local image_name=$2
    
    if grep -q "image: $image_name" "$file" && ! grep -q "imagePullPolicy: Never" "$file"; then
        echo "Adding imagePullPolicy: Never to $file for $image_name"
        sed -i.bak "s/image: $image_name/image: $image_name\n        imagePullPolicy: Never/" "$file"
    fi
}

# Fix image pull policies for local images
echo "📝 Updating image pull policies..."

# Fix trading-service
add_image_pull_policy "k8s/trading-service.yaml" "trading-service:latest"

# Fix health-dashboard (already has imagePullPolicy: Never)

# Fix trading-bot images in various files
for file in k8s/*.yaml; do
    if grep -q "image: trading-bot:latest" "$file"; then
        add_image_pull_policy "$file" "trading-bot:latest"
    fi
done

# Create missing PVC for dev namespace
echo "🗄️ Creating missing PVC for dev namespace..."
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: db-pvc
  namespace: dev
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: hostpath
  resources:
    requests:
      storage: 1Gi
EOF

# Restart failing deployments
echo "🔄 Restarting failing deployments..."

# Restart health-dashboard
kubectl rollout restart deployment/health-dashboard -n trading-system

# Restart trading-service
kubectl rollout restart deployment/trading-service -n trading-system

# Restart dev namespace deployments
kubectl rollout restart deployment/db -n dev
kubectl rollout restart deployment/redis -n dev
kubectl rollout restart deployment/worker -n dev

# Wait for deployments to be ready
echo "⏳ Waiting for deployments to be ready..."
kubectl rollout status deployment/health-dashboard -n trading-system --timeout=300s
kubectl rollout status deployment/trading-service -n trading-system --timeout=300s

# Clean up old failed pods
echo "🧹 Cleaning up old failed pods..."
kubectl delete pods --field-selector=status.phase=Failed --all-namespaces

# Show current status
echo "📊 Current pod status:"
kubectl get pods --all-namespaces | grep -E "(Pending|Error|ImagePullBackOff|CrashLoopBackOff)"

echo "✅ Fix completed! Check pod status with: kubectl get pods --all-namespaces" 