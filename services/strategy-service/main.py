from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from prometheus_client import generate_latest, Counter, Histogram, Gauge
from fastapi.responses import Response

app = FastAPI(title="Strategy Service", version="1.0.0")

# Prometheus metrics
strategy_requests_total = Counter("strategy_requests_total", "Total number of strategy requests")
strategy_request_duration = Histogram("strategy_request_duration_seconds", "Time spent on strategy requests")

class Strategy(BaseModel):
    name: str
    type: str
    parameters: dict

@app.get("/")
async def root():
    strategy_requests_total.inc()
    return {"message": "Strategy Service is running"}

@app.get("/health")
async def health():
    strategy_requests_total.inc()
    return {"status": "healthy"}

@app.get("/ready")
async def ready():
    strategy_requests_total.inc()
    return {"status": "ready"}

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")

@app.post("/api/v1/strategies")
async def create_strategy(strategy: Strategy):
    strategy_requests_total.inc()
    return {"message": "Strategy created", "strategy": strategy}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
