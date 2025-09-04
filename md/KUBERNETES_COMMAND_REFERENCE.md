# 🚀 Kubernetes Command Reference

## 📋 **Quick Navigation**
- [Basic Commands](#basic-commands)
- [Pod Operations](#pod-operations)
- [Deployment Operations](#deployment-operations)
- [Service Operations](#service-operations)
- [ConfigMap & Secrets](#configmap--secrets)
- [Job & CronJob](#job--cronjob)
- [Debugging & Troubleshooting](#debugging--troubleshooting)
- [Resource Management](#resource-management)
- [Your Project Commands](#your-project-commands)

---

## 🔧 **Basic Commands**

### **Cluster Information**
```bash
# Check cluster info
kubectl cluster-info

# Get nodes
kubectl get nodes

# Get namespaces
kubectl get namespaces

# Set default namespace
kubectl config set-context --current --namespace=trading-system
```

### **Context Management**
```bash
# List contexts
kubectl config get-contexts

# Switch context
kubectl config use-context <context-name>

# View current context
kubectl config current-context
```

---

## 🐳 **Pod Operations**

### **Create & Manage Pods**
```bash
# Create pod from YAML
kubectl apply -f pod.yaml

# Create pod directly
kubectl run nginx-pod --image=nginx:alpine

# Get pods
kubectl get pods -n trading-system

# Get pods with labels
kubectl get pods -l app=myapp -n trading-system

# Describe pod
kubectl describe pod <pod-name> -n trading-system

# Delete pod
kubectl delete pod <pod-name> -n trading-system
```

### **Pod Interaction**
```bash
# View pod logs
kubectl logs <pod-name> -n trading-system

# Follow logs
kubectl logs -f <pod-name> -n trading-system

# Execute command in pod
kubectl exec -it <pod-name> -n trading-system -- /bin/bash

# Copy file from/to pod
kubectl cp <pod-name>:/path/to/file ./local-file -n trading-system
kubectl cp ./local-file <pod-name>:/path/to/file -n trading-system
```

---

## 🚀 **Deployment Operations**

### **Create & Manage Deployments**
```bash
# Create deployment
kubectl apply -f deployment.yaml

# Get deployments
kubectl get deployments -n trading-system

# Scale deployment
kubectl scale deployment <deployment-name> --replicas=3 -n trading-system

# Update deployment image
kubectl set image deployment/<deployment-name> <container-name>=<new-image> -n trading-system

# Delete deployment
kubectl delete deployment <deployment-name> -n trading-system
```

### **Rollout Management**
```bash
# Check rollout status
kubectl rollout status deployment/<deployment-name> -n trading-system

# Pause rollout
kubectl rollout pause deployment/<deployment-name> -n trading-system

# Resume rollout
kubectl rollout resume deployment/<deployment-name> -n trading-system

# Rollback to previous version
kubectl rollout undo deployment/<deployment-name> -n trading-system

# Rollback to specific version
kubectl rollout undo deployment/<deployment-name> --to-revision=2 -n trading-system

# View rollout history
kubectl rollout history deployment/<deployment-name> -n trading-system
```

---

## 🌐 **Service Operations**

### **Create & Manage Services**
```bash
# Create service
kubectl apply -f service.yaml

# Get services
kubectl get services -n trading-system

# Describe service
kubectl describe service <service-name> -n trading-system

# Delete service
kubectl delete service <service-name> -n trading-system
```

### **Port Forwarding**
```bash
# Port forward service
kubectl port-forward service/<service-name> 8080:80 -n trading-system

# Port forward pod
kubectl port-forward <pod-name> 8080:80 -n trading-system

# Port forward with specific address
kubectl port-forward service/<service-name> 8080:80 --address=0.0.0.0 -n trading-system
```

---

## 🔐 **ConfigMap & Secrets**

### **ConfigMap Operations**
```bash
# Create ConfigMap from file
kubectl create configmap <name> --from-file=config.properties -n trading-system

# Create ConfigMap from literal
kubectl create configmap <name> --from-literal=key1=value1 --from-literal=key2=value2 -n trading-system

# Get ConfigMaps
kubectl get configmaps -n trading-system

# Describe ConfigMap
kubectl describe configmap <name> -n trading-system

# Delete ConfigMap
kubectl delete configmap <name> -n trading-system
```

### **Secret Operations**
```bash
# Create secret from file
kubectl create secret generic <name> --from-file=secret.txt -n trading-system

# Create secret from literal
kubectl create secret generic <name> --from-literal=username=admin --from-literal=password=secret -n trading-system

# Get secrets
kubectl get secrets -n trading-system

# Describe secret
kubectl describe secret <name> -n trading-system

# Delete secret
kubectl delete secret <name> -n trading-system
```

---

## ⏰ **Job & CronJob**

### **Job Operations**
```bash
# Create job
kubectl apply -f job.yaml

# Get jobs
kubectl get jobs -n trading-system

# View job logs
kubectl logs job/<job-name> -n trading-system

# Delete job
kubectl delete job <job-name> -n trading-system
```

### **CronJob Operations**
```bash
# Create CronJob
kubectl apply -f cronjob.yaml

# Get CronJobs
kubectl get cronjobs -n trading-system

# Suspend CronJob
kubectl patch cronjob <name> -p '{"spec" : {"suspend" : true }}' -n trading-system

# Resume CronJob
kubectl patch cronjob <name> -p '{"spec" : {"suspend" : false }}' -n trading-system

# Delete CronJob
kubectl delete cronjob <name> -n trading-system
```

---

## 🔍 **Debugging & Troubleshooting**

### **Pod Debugging**
```bash
# Get pod events
kubectl get events -n trading-system --sort-by='.lastTimestamp'

# Get pod events for specific pod
kubectl get events -n trading-system --field-selector involvedObject.name=<pod-name>

# Check pod status
kubectl get pods -n trading-system -o wide

# Get pod YAML
kubectl get pod <pod-name> -n trading-system -o yaml

# Edit pod (not recommended for running pods)
kubectl edit pod <pod-name> -n trading-system
```

### **Service Debugging**
```bash
# Test service connectivity
kubectl run test-client --image=busybox --rm -it --restart=Never -n trading-system -- wget -O- <service-name>:<port>

# Get service endpoints
kubectl get endpoints <service-name> -n trading-system

# Describe service endpoints
kubectl describe endpoints <service-name> -n trading-system
```

### **Network Debugging**
```bash
# Check DNS resolution
kubectl run test-dns --image=busybox --rm -it --restart=Never -n trading-system -- nslookup <service-name>

# Test network connectivity
kubectl run test-connectivity --image=busybox --rm -it --restart=Never -n trading-system -- ping <service-name>
```

---

## 📊 **Resource Management**

### **Resource Monitoring**
```bash
# Get resource usage for pods
kubectl top pods -n trading-system

# Get resource usage for nodes
kubectl top nodes

# Get resource usage for specific pod
kubectl top pod <pod-name> -n trading-system
```

### **Resource Quotas**
```bash
# Get resource quotas
kubectl get resourcequota -n trading-system

# Describe resource quota
kubectl describe resourcequota <name> -n trading-system
```

### **Horizontal Pod Autoscaler**
```bash
# Get HPA
kubectl get hpa -n trading-system

# Describe HPA
kubectl describe hpa <name> -n trading-system

# Create HPA
kubectl autoscale deployment <deployment-name> --cpu-percent=50 --min=1 --max=10 -n trading-system
```

---

## 🎯 **Your Project Commands**

### **Using Your Makefiles**
```bash
# Deploy services
make -f Makefile.kubernetes k8s-deploy-strategy-service
make -f Makefile.kubernetes k8s-deploy-market-data-worker

# Check status
make -f Makefile.kubernetes k8s-status
make -f Makefile.kubernetes k8s-status-strategy

# View logs
make -f Makefile.kubernetes k8s-logs
make -f Makefile.kubernetes k8s-logs-strategy

# Port forwarding
make -f Makefile.kubernetes k8s-port-forward-start
make -f Makefile.kubernetes k8s-port-forward-status
```

### **Job Generation**
```bash
# Generate backtest job
make -f Makefile.kubernetes k8s-job-backtest SCRIPT=scripts/backtest_cli.py NAME=my-backtest APPLY=true

# Generate analysis job
make -f Makefile.kubernetes k8s-job-analysis SCRIPT=scripts/analyze_winning_strategies.py NAME=my-analysis APPLY=true

# Quick jobs
make -f Makefile.kubernetes k8s-quick-backtest
make -f Makefile.kubernetes k8s-quick-analysis
```

### **Learning Exercises**
```bash
# Run learning exercises
./scripts/k8s-learning-exercises.sh

# View learning guide
make k8s-learn-preview
make k8s-learn
```

---

## 🎨 **Useful Aliases**

Add these to your `~/.bashrc` or `~/.zshrc`:

```bash
# Quick access to trading-system namespace
alias k='kubectl -n trading-system'

# Get all resources
alias kg='kubectl get -n trading-system'

# Get pods
alias kgp='kubectl get pods -n trading-system'

# Get services
alias kgs='kubectl get services -n trading-system'

# Get deployments
alias kgd='kubectl get deployments -n trading-system'

# Describe pod
alias kdp='kubectl describe pod -n trading-system'

# Logs with follow
alias klf='kubectl logs -f -n trading-system'

# Port forward
alias kpf='kubectl port-forward -n trading-system'
```

---

## 🚨 **Emergency Commands**

### **Quick Cleanup**
```bash
# Delete all resources in namespace
kubectl delete all --all -n trading-system

# Delete specific resource type
kubectl delete pods --all -n trading-system
kubectl delete deployments --all -n trading-system
kubectl delete services --all -n trading-system
```

### **Force Delete**
```bash
# Force delete pod
kubectl delete pod <pod-name> --grace-period=0 --force -n trading-system

# Force delete deployment
kubectl delete deployment <deployment-name> --grace-period=0 --force -n trading-system
```

---

## 📚 **Learning Resources**

### **Your Project Resources**
- `KUBERNETES_LEARNING_PLAN.md` - Your personalized learning plan
- `docs/KUBERNETES_LEARNING_GUIDE.md` - Comprehensive guide
- `scripts/k8s-learning-exercises.sh` - Hands-on exercises
- `k8s/README.md` - Your cluster documentation

### **External Resources**
- [Kubernetes Official Documentation](https://kubernetes.io/docs/)
- [Kubernetes Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Kubernetes by Example](https://kubernetesbyexample.com/)

---

## 🎯 **Pro Tips**

1. **Always specify namespace**: Use `-n trading-system` or set it as default
2. **Use labels**: Organize resources with meaningful labels
3. **Check events**: Use `kubectl get events` for troubleshooting
4. **Use YAML output**: Add `-o yaml` to see full resource definitions
5. **Practice regularly**: Use your learning exercises daily
6. **Monitor resources**: Keep an eye on resource usage with `kubectl top`

Remember: **Practice makes perfect!** Use this reference guide alongside your hands-on exercises to master Kubernetes. 🚀
