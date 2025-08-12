# 🚀 Kubernetes Commands Reference for Trading System

## 📋 Quick Reference Commands

### **System Status & Overview**
```bash
# Check all resources in trading-system namespace
kubectl get all -n trading-system

# Check pod status
kubectl get pods -n trading-system

# Check service status
kubectl get services -n trading-system

# Check deployment status
kubectl get deployments -n trading-system

# Check configmaps and secrets
kubectl get configmaps,secrets -n trading-system
```

### **Service Management**
```bash
# Scale a service
kubectl scale deployment service-name --replicas=3 -n trading-system

# Restart a service
kubectl rollout restart deployment service-name -n trading-system

# Check rollout status
kubectl rollout status deployment service-name -n trading-system

# Rollback to previous version
kubectl rollout undo deployment service-name -n trading-system
```

## 🔍 Detailed Commands by Category

### **1. Pod Management**

#### **View Pods**
```bash
# List all pods
kubectl get pods -n trading-system

# List pods with labels
kubectl get pods -l app=service-name -n trading-system

# List pods with wide output
kubectl get pods -o wide -n trading-system

# List pods with custom columns
kubectl get pods -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,READY:.status.readyReplicas -n trading-system
```

#### **Pod Details**
```bash
# Describe pod details
kubectl describe pod pod-name -n trading-system

# View pod logs
kubectl logs pod-name -n trading-system

# Follow pod logs
kubectl logs -f pod-name -n trading-system

# View logs from previous container restart
kubectl logs pod-name --previous -n trading-system
```

#### **Pod Interaction**
```bash
# Execute command in pod
kubectl exec -it pod-name -- /bin/bash -n trading-system

# Execute command without interactive shell
kubectl exec pod-name -- command -n trading-system

# Copy files to/from pod
kubectl cp local-file pod-name:/remote-path -n trading-system
kubectl cp pod-name:/remote-path local-file -n trading-system
```

### **2. Service Management**

#### **View Services**
```bash
# List all services
kubectl get services -n trading-system

# Describe service details
kubectl describe service service-name -n trading-system

# Check service endpoints
kubectl get endpoints -n trading-system

# Check service endpoints for specific service
kubectl get endpoints service-name -n trading-system
```

#### **Service Configuration**
```bash
# Edit service configuration
kubectl edit service service-name -n trading-system

# Patch service configuration
kubectl patch service service-name -p '{"spec":{"type":"LoadBalancer"}}' -n trading-system

# Delete service
kubectl delete service service-name -n trading-system
```

### **3. Deployment Management**

#### **View Deployments**
```bash
# List all deployments
kubectl get deployments -n trading-system

# Describe deployment details
kubectl describe deployment deployment-name -n trading-system

# Check deployment history
kubectl rollout history deployment deployment-name -n trading-system
```

#### **Deployment Operations**
```bash
# Update deployment image
kubectl set image deployment/deployment-name container-name=new-image:tag -n trading-system

# Pause deployment
kubectl rollout pause deployment deployment-name -n trading-system

# Resume deployment
kubectl rollout resume deployment deployment-name -n trading-system

# Check deployment status
kubectl rollout status deployment deployment-name -n trading-system
```

### **4. Configuration Management**

#### **ConfigMaps**
```bash
# List configmaps
kubectl get configmaps -n trading-system

# Describe configmap
kubectl describe configmap configmap-name -n trading-system

# View configmap data
kubectl get configmap configmap-name -o yaml -n trading-system

# Create configmap from file
kubectl create configmap configmap-name --from-file=file.txt -n trading-system

# Create configmap from literal values
kubectl create configmap configmap-name --from-literal=key1=value1 --from-literal=key2=value2 -n trading-system
```

#### **Secrets**
```bash
# List secrets
kubectl get secrets -n trading-system

# Describe secret
kubectl describe secret secret-name -n trading-system

# View secret data (base64 encoded)
kubectl get secret secret-name -o yaml -n trading-system

# Create secret from literal values
kubectl create secret generic secret-name --from-literal=username=admin --from-literal=password=secret123 -n trading-system

# Create secret from file
kubectl create secret generic secret-name --from-file=./username.txt --from-file=./password.txt -n trading-system
```

### **5. Resource Monitoring**

#### **Resource Usage**
```bash
# Check pod resource usage
kubectl top pods -n trading-system

# Check node resource usage
kubectl top nodes

# Check resource usage for specific pod
kubectl top pod pod-name -n trading-system
```

#### **Events & Logs**
```bash
# View cluster events
kubectl get events -n trading-system

# View events for specific resource
kubectl get events --field-selector involvedObject.name=pod-name -n trading-system

# View events sorted by time
kubectl get events --sort-by=.metadata.creationTimestamp -n trading-system
```

### **6. Port Forwarding & Access**

#### **Port Forwarding**
```bash
# Forward service to local port
kubectl port-forward service/service-name local-port:service-port -n trading-system

# Forward pod to local port
kubectl port-forward pod/pod-name local-port:pod-port -n trading-system

# Forward deployment to local port
kubectl port-forward deployment/deployment-name local-port:deployment-port -n trading-system
```

#### **Service Access**
```bash
# Test service endpoint
kubectl run test-pod --image=busybox --restart=Never --rm -it -- wget -qO- http://service-name

# Check service connectivity
kubectl run test-pod --image=busybox --restart=Never --rm -it -- nslookup service-name
```

### **7. Troubleshooting Commands**

#### **Network Issues**
```bash
# Check DNS resolution
kubectl run test-pod --image=busybox --restart=Never --rm -it -- nslookup kubernetes.default

# Test network connectivity
kubectl run test-pod --image=busybox --restart=Never --rm -it -- ping service-name

# Check network policies
kubectl get networkpolicies -n trading-system
```

#### **Storage Issues**
```bash
# Check persistent volumes
kubectl get pv

# Check persistent volume claims
kubectl get pvc -n trading-system

# Check storage classes
kubectl get storageclass
```

### **8. Advanced Commands**

#### **Resource Quotas & Limits**
```bash
# Check resource quotas
kubectl get resourcequota -n trading-system

# Check limit ranges
kubectl get limitrange -n trading-system

# Check resource usage against quotas
kubectl describe resourcequota resourcequota-name -n trading-system
```

#### **RBAC & Security**
```bash
# Check service accounts
kubectl get serviceaccounts -n trading-system

# Check roles and role bindings
kubectl get roles,rolebindings -n trading-system

# Check cluster roles and bindings
kubectl get clusterroles,clusterrolebindings
```

## 🎯 Trading System Specific Commands

### **Check Trading System Health**
```bash
# Check all trading services
kubectl get pods -l app=trading-core-service -n trading-system
kubectl get pods -l app=strategy-service -n trading-system
kubectl get pods -l app=market-data-service -n trading-system

# Check dashboard services
kubectl get pods -l app=unified-analytics-dashboard -n trading-system
kubectl get pods -l app=unified-trading-dashboard -n trading-system
kubectl get pods -l app=unified-news-dashboard -n trading-system

# Check infrastructure services
kubectl get pods -l app=postgres -n trading-system
kubectl get pods -l app=redis -n trading-system
kubectl get pods -l app=rabbitmq -n trading-system
```

### **Monitor Trading System Performance**
```bash
# Check resource usage across all services
kubectl top pods -n trading-system --sort-by=cpu
kubectl top pods -n trading-system --sort-by=memory

# Check service endpoints
kubectl get endpoints -n trading-system

# Check service load balancing
kubectl describe service service-name -n trading-system
```

### **Trading System Maintenance**
```bash
# Restart all trading services
kubectl rollout restart deployment -l app=trading-core-service -n trading-system
kubectl rollout restart deployment -l app=strategy-service -n trading-system
kubectl rollout restart deployment -l app=market-data-service -n trading-system

# Check rollout status
kubectl rollout status deployment -l app=trading-core-service -n trading-system

# Scale trading services
kubectl scale deployment trading-core-service --replicas=3 -n trading-system
```

## 🚨 Emergency Commands

### **Quick Recovery**
```bash
# Force delete stuck pods
kubectl delete pod pod-name --force --grace-period=0 -n trading-system

# Restart all deployments in namespace
kubectl rollout restart deployment --all -n trading-system

# Check and fix node issues
kubectl cordon node-name
kubectl drain node-name --ignore-daemonsets --delete-emptydir-data
```

### **Debug Mode**
```bash
# Enable debug logging
kubectl patch deployment deployment-name -p '{"spec":{"template":{"spec":{"containers":[{"name":"container-name","env":[{"name":"LOG_LEVEL","value":"DEBUG"}]}]}}}}' -n trading-system

# Check pod events
kubectl get events --field-selector involvedObject.name=pod-name --sort-by=.metadata.creationTimestamp -n trading-system
```

## 📚 Useful Aliases

Add these to your shell profile for quick access:
```bash
# Quick namespace access
alias k='kubectl'
alias kns='kubectl config set-context --current --namespace'

# Quick pod access
alias kp='kubectl get pods'
alias kpl='kubectl get pods -l app='
alias kpf='kubectl port-forward'

# Quick service access
alias ks='kubectl get services'
alias kd='kubectl get deployments'

# Quick logs
alias kl='kubectl logs'
alias klf='kubectl logs -f'
```

## 🔧 Best Practices

1. **Always specify namespace** with `-n trading-system`
2. **Use labels** for filtering resources
3. **Check resource usage** before scaling
4. **Monitor rollout status** after changes
5. **Use port forwarding** for local development
6. **Check logs** for troubleshooting
7. **Verify endpoints** for service connectivity
8. **Use resource limits** to prevent issues
