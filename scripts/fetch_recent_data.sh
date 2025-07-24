#!/bin/bash

echo "Fetching data for all symbols (last 30 days)..."

kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: data-fetch-recent
  namespace: trading-system
spec:
  template:
    spec:
      containers:
      - name: data-fetcher
        image: localhost:5000/strategy-service:latest
        command: ["python", "scripts/fetch_data.py", "recent"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: trading-secrets
              key: database-url
        - name: POLYGON_API_KEY
          valueFrom:
            secretKeyRef:
              name: trading-secrets
              key: polygon-api-key
      restartPolicy: Never
EOF

echo "Data fetch job created. Check logs with: kubectl logs job/data-fetch-recent -n trading-system" 