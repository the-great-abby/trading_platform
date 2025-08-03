from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from prometheus_client import generate_latest, Counter, Histogram, Gauge
from fastapi.responses import Response

app = FastAPI(title="Public API Service", version="1.0.0")

# Prometheus metrics
service_requests_total = Counter("service_requests_total", "Total number of service requests")
service_request_duration = Histogram("service_request_duration_seconds", "Time spent on service requests")

class TradingSignal(BaseModel):
    symbol: str
    action: str
    price: float
    quantity: int
    strategy: str

@app.get("/")
async def root():
    service_requests_total.inc()
    return {"message": "Public API Service is running"}

@app.get("/health")
async def health():
    service_requests_total.inc()
    return {"status": "healthy"}

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")

@app.post("/api/v1/signals")
async def create_signal(signal: TradingSignal):
    # This would integrate with external trading APIs
    return {
        "message": "Signal received",
        "signal": signal.dict(),
        "status": "pending"
    }

@app.get("/api/v1/status")
async def get_status():
    return {
        "service": "public-api",
        "version": "1.0.0",
        "status": "operational"
    } 