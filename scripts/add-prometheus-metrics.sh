#!/bin/bash

# Add Prometheus metrics to services that don't have them

echo "Adding Prometheus metrics to services..."

# Services that need metrics endpoints
SERVICES=("user-service" "public-api" "order-service" "portfolio-service" "strategy-service")

for service in "${SERVICES[@]}"; do
    echo "Adding metrics to $service..."
    
    # Add import and metrics to main.py
    sed -i '' '1s/^/from prometheus_client import generate_latest, Counter, Histogram, Gauge\nimport time\n/' "services/$service/main.py"
    
    # Add metrics definitions after app creation
    sed -i '' '/app = FastAPI/a\
# Prometheus metrics\
service_requests_total = Counter("service_requests_total", "Total number of service requests")\
service_request_duration = Histogram("service_request_duration_seconds", "Time spent on service requests")\
' "services/$service/main.py"
    
    # Add metrics endpoint at the end before if __name__ == "__main__"
    sed -i '' '/if __name__ == "__main__":/i\
@app.get("/metrics")\
async def get_metrics():\
    """Prometheus metrics endpoint"""\
    return generate_latest()\
' "services/$service/main.py"
    
    echo "✅ Added metrics to $service"
done

echo "✅ All services updated with Prometheus metrics" 