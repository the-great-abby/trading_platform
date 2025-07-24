#!/bin/bash

# Usage: ./fetch_custom_data.sh SYMBOLS START_DATE END_DATE
# Example: ./fetch_custom_data.sh "AAPL,MSFT,GOOGL" "2024-01-01" "2024-12-31"

SYMBOLS=${1:-"AAPL,MSFT,GOOGL"}
START_DATE=${2:-"2024-01-01"}
END_DATE=${3:-"2025-07-23"}

echo "Fetching data for symbols: $SYMBOLS"
echo "Date range: $START_DATE to $END_DATE"

kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: data-fetch-custom
  namespace: trading-system
spec:
  template:
    spec:
      containers:
      - name: data-fetcher
        image: localhost:5000/strategy-service:latest
        command: ["python", "scripts/fetch_data.py", "custom", "--symbols", "$SYMBOLS", "--start-date", "$START_DATE", "--end-date", "$END_DATE"]
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

echo "Data fetch job created. Check logs with: kubectl logs job/data-fetch-custom -n trading-system" 