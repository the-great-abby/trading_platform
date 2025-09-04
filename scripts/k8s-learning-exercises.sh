#!/bin/bash

# 🎓 Kubernetes Learning Exercises
# This script provides hands-on exercises to improve your Kubernetes skills

set -e

NAMESPACE="trading-system"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🎓 Kubernetes Learning Exercises${NC}"
echo "=================================="

# Function to print section headers
print_section() {
    echo -e "\n${YELLOW}$1${NC}"
    echo "----------------------------------------"
}

# Function to wait for user input
wait_for_user() {
    echo -e "\n${GREEN}Press Enter to continue...${NC}"
    read -r
}

# Exercise 1: Basic Pod Operations
exercise_1() {
    print_section "Exercise 1: Basic Pod Operations"
    
    echo "1. Creating a simple test pod..."
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
  namespace: $NAMESPACE
spec:
  containers:
  - name: nginx
    image: nginx:alpine
    ports:
    - containerPort: 80
EOF

    echo -e "\n2. Checking pod status..."
    kubectl get pods -n $NAMESPACE | grep test-pod
    
    echo -e "\n3. Getting detailed pod information..."
    kubectl describe pod test-pod -n $NAMESPACE
    
    echo -e "\n4. Viewing pod logs..."
    kubectl logs test-pod -n $NAMESPACE
    
    echo -e "\n5. Executing a command in the pod..."
    kubectl exec -it test-pod -n $NAMESPACE -- nginx -v
    
    wait_for_user
    
    echo "6. Cleaning up test pod..."
    kubectl delete pod test-pod -n $NAMESPACE
}

# Exercise 2: Deployment Operations
exercise_2() {
    print_section "Exercise 2: Deployment Operations"
    
    echo "1. Creating a deployment..."
    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-deployment
  namespace: $NAMESPACE
spec:
  replicas: 2
  selector:
    matchLabels:
      app: test-app
  template:
    metadata:
      labels:
        app: test-app
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
EOF

    echo -e "\n2. Checking deployment status..."
    kubectl get deployments -n $NAMESPACE | grep test-deployment
    
    echo -e "\n3. Scaling the deployment..."
    kubectl scale deployment test-deployment --replicas=3 -n $NAMESPACE
    
    echo -e "\n4. Checking pod status after scaling..."
    kubectl get pods -n $NAMESPACE | grep test-deployment
    
    echo -e "\n5. Updating the deployment image..."
    kubectl set image deployment/test-deployment nginx=nginx:1.21 -n $NAMESPACE
    
    echo -e "\n6. Checking rollout status..."
    kubectl rollout status deployment/test-deployment -n $NAMESPACE
    
    wait_for_user
    
    echo "7. Rolling back the deployment..."
    kubectl rollout undo deployment/test-deployment -n $NAMESPACE
    
    echo -e "\n8. Cleaning up deployment..."
    kubectl delete deployment test-deployment -n $NAMESPACE
}

# Exercise 3: Service Operations
exercise_3() {
    print_section "Exercise 3: Service Operations"
    
    echo "1. Creating a deployment for service testing..."
    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: service-test
  namespace: $NAMESPACE
spec:
  replicas: 2
  selector:
    matchLabels:
      app: service-test
  template:
    metadata:
      labels:
        app: service-test
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
        ports:
        - containerPort: 80
EOF

    echo -e "\n2. Creating a ClusterIP service..."
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: service-test-clusterip
  namespace: $NAMESPACE
spec:
  type: ClusterIP
  selector:
    app: service-test
  ports:
  - port: 80
    targetPort: 80
EOF

    echo -e "\n3. Creating a NodePort service..."
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: service-test-nodeport
  namespace: $NAMESPACE
spec:
  type: NodePort
  selector:
    app: service-test
  ports:
  - port: 80
    targetPort: 80
    nodePort: 30080
EOF

    echo -e "\n4. Checking service status..."
    kubectl get services -n $NAMESPACE | grep service-test
    
    echo -e "\n5. Getting detailed service information..."
    kubectl describe service service-test-clusterip -n $NAMESPACE
    
    echo -e "\n6. Testing service connectivity..."
    kubectl run test-client --image=busybox --rm -it --restart=Never -n $NAMESPACE -- wget -O- service-test-clusterip:80
    
    wait_for_user
    
    echo "7. Cleaning up services and deployment..."
    kubectl delete service service-test-clusterip -n $NAMESPACE
    kubectl delete service service-test-nodeport -n $NAMESPACE
    kubectl delete deployment service-test -n $NAMESPACE
}

# Exercise 4: ConfigMap and Secrets
exercise_4() {
    print_section "Exercise 4: ConfigMap and Secrets"
    
    echo "1. Creating a ConfigMap..."
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: test-config
  namespace: $NAMESPACE
data:
  database_url: "postgresql://localhost:5432/testdb"
  api_version: "v1"
  debug_mode: "true"
EOF

    echo -e "\n2. Creating a Secret..."
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: test-secret
  namespace: $NAMESPACE
type: Opaque
data:
  username: YWRtaW4=  # admin
  password: cGFzc3dvcmQ=  # password
EOF

    echo -e "\n3. Creating a pod that uses ConfigMap and Secret..."
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: config-test-pod
  namespace: $NAMESPACE
spec:
  containers:
  - name: nginx
    image: nginx:alpine
    env:
    - name: DATABASE_URL
      valueFrom:
        configMapKeyRef:
          name: test-config
          key: database_url
    - name: API_VERSION
      valueFrom:
        configMapKeyRef:
          name: test-config
          key: api_version
    - name: USERNAME
      valueFrom:
        secretKeyRef:
          name: test-secret
          key: username
    - name: PASSWORD
      valueFrom:
        secretKeyRef:
          name: test-secret
          key: password
    command: ["sh", "-c", "echo 'Database URL: \$DATABASE_URL'; echo 'API Version: \$API_VERSION'; echo 'Username: \$USERNAME'; echo 'Password: \$PASSWORD'; sleep 3600"]
EOF

    echo -e "\n4. Checking the pod..."
    kubectl get pods -n $NAMESPACE | grep config-test-pod
    
    echo -e "\n5. Viewing environment variables..."
    kubectl exec config-test-pod -n $NAMESPACE -- env | grep -E "(DATABASE_URL|API_VERSION|USERNAME|PASSWORD)"
    
    wait_for_user
    
    echo "6. Cleaning up..."
    kubectl delete pod config-test-pod -n $NAMESPACE
    kubectl delete configmap test-config -n $NAMESPACE
    kubectl delete secret test-secret -n $NAMESPACE
}

# Exercise 5: Job and CronJob
exercise_5() {
    print_section "Exercise 5: Job and CronJob"
    
    echo "1. Creating a simple Job..."
    cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: test-job
  namespace: $NAMESPACE
spec:
  template:
    spec:
      containers:
      - name: job-container
        image: busybox
        command: ["sh", "-c", "echo 'Job completed successfully!'; date"]
      restartPolicy: Never
  backoffLimit: 3
EOF

    echo -e "\n2. Checking job status..."
    kubectl get jobs -n $NAMESPACE | grep test-job
    
    echo -e "\n3. Viewing job logs..."
    kubectl logs job/test-job -n $NAMESPACE
    
    echo -e "\n4. Creating a CronJob..."
    cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: CronJob
metadata:
  name: test-cronjob
  namespace: $NAMESPACE
spec:
  schedule: "*/2 * * * *"  # Every 2 minutes
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: cronjob-container
            image: busybox
            command: ["sh", "-c", "echo 'CronJob executed at:'; date"]
          restartPolicy: OnFailure
EOF

    echo -e "\n5. Checking CronJob status..."
    kubectl get cronjobs -n $NAMESPACE | grep test-cronjob
    
    echo -e "\n6. Viewing CronJob jobs..."
    kubectl get jobs -n $NAMESPACE | grep test-cronjob
    
    wait_for_user
    
    echo "7. Cleaning up..."
    kubectl delete job test-job -n $NAMESPACE
    kubectl delete cronjob test-cronjob -n $NAMESPACE
}

# Exercise 6: Debugging and Troubleshooting
exercise_6() {
    print_section "Exercise 6: Debugging and Troubleshooting"
    
    echo "1. Creating a problematic deployment..."
    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: problematic-deployment
  namespace: $NAMESPACE
spec:
  replicas: 1
  selector:
    matchLabels:
      app: problematic
  template:
    metadata:
      labels:
        app: problematic
    spec:
      containers:
      - name: problematic-container
        image: nginx:invalid-tag
        ports:
        - containerPort: 80
EOF

    echo -e "\n2. Checking deployment status..."
    kubectl get deployments -n $NAMESPACE | grep problematic
    
    echo -e "\n3. Checking pod status..."
    kubectl get pods -n $NAMESPACE | grep problematic
    
    echo -e "\n4. Describing the pod to see issues..."
    kubectl describe pod -l app=problematic -n $NAMESPACE
    
    echo -e "\n5. Viewing pod events..."
    kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' | grep problematic
    
    echo -e "\n6. Fixing the deployment..."
    kubectl set image deployment/problematic-deployment problematic-container=nginx:alpine -n $NAMESPACE
    
    echo -e "\n7. Checking if the fix worked..."
    kubectl get pods -n $NAMESPACE | grep problematic
    
    wait_for_user
    
    echo "8. Cleaning up..."
    kubectl delete deployment problematic-deployment -n $NAMESPACE
}

# Exercise 7: Resource Management
exercise_7() {
    print_section "Exercise 7: Resource Management"
    
    echo "1. Creating a deployment with resource limits..."
    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: resource-test
  namespace: $NAMESPACE
spec:
  replicas: 1
  selector:
    matchLabels:
      app: resource-test
  template:
    metadata:
      labels:
        app: resource-test
    spec:
      containers:
      - name: resource-container
        image: nginx:alpine
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
        ports:
        - containerPort: 80
EOF

    echo -e "\n2. Checking resource usage..."
    kubectl top pods -n $NAMESPACE | grep resource-test
    
    echo -e "\n3. Describing pod to see resource configuration..."
    kubectl describe pod -l app=resource-test -n $NAMESPACE | grep -A 10 "Containers:"
    
    echo -e "\n4. Scaling the deployment..."
    kubectl scale deployment resource-test --replicas=3 -n $NAMESPACE
    
    echo -e "\n5. Checking resource usage after scaling..."
    kubectl top pods -n $NAMESPACE | grep resource-test
    
    wait_for_user
    
    echo "6. Cleaning up..."
    kubectl delete deployment resource-test -n $NAMESPACE
}

# Main menu
show_menu() {
    echo -e "\n${GREEN}Available Exercises:${NC}"
    echo "1. Basic Pod Operations"
    echo "2. Deployment Operations"
    echo "3. Service Operations"
    echo "4. ConfigMap and Secrets"
    echo "5. Job and CronJob"
    echo "6. Debugging and Troubleshooting"
    echo "7. Resource Management"
    echo "8. Run All Exercises"
    echo "9. Exit"
    echo -e "\nEnter your choice (1-9): "
}

# Main execution
main() {
    while true; do
        show_menu
        read -r choice
        
        case $choice in
            1) exercise_1 ;;
            2) exercise_2 ;;
            3) exercise_3 ;;
            4) exercise_4 ;;
            5) exercise_5 ;;
            6) exercise_6 ;;
            7) exercise_7 ;;
            8)
                echo -e "\n${GREEN}Running all exercises...${NC}"
                exercise_1
                exercise_2
                exercise_3
                exercise_4
                exercise_5
                exercise_6
                exercise_7
                ;;
            9)
                echo -e "\n${GREEN}Goodbye! Keep practicing Kubernetes! 🚀${NC}"
                exit 0
                ;;
            *)
                echo -e "\n${RED}Invalid choice. Please enter 1-9.${NC}"
                ;;
        esac
    done
}

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed or not in PATH${NC}"
    exit 1
fi

# Check if namespace exists
if ! kubectl get namespace $NAMESPACE &> /dev/null; then
    echo -e "${RED}Error: Namespace '$NAMESPACE' does not exist${NC}"
    echo "Please create the namespace first: kubectl create namespace $NAMESPACE"
    exit 1
fi

# Run main function
main
