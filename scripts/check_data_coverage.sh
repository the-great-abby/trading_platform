#!/bin/bash

echo "Checking data coverage for all symbols..."

kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: data-coverage-check
  namespace: trading-system
spec:
  template:
    spec:
      containers:
      - name: coverage-checker
        image: localhost:5000/strategy-service:latest
        command: ["python", "scripts/fetch_data.py", "coverage"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: trading-secrets
              key: database-url
      restartPolicy: Never
EOF

echo "Coverage check job created. Check logs with: kubectl logs job/data-coverage-check -n trading-system" 