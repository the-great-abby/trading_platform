from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from prometheus_client import generate_latest, Counter, Histogram, Gauge
from fastapi.responses import Response

app = FastAPI(title="Order Service", version="1.0.0")

# Prometheus metrics
order_requests_total = Counter("order_requests_total", "Total number of order requests")
order_request_duration = Histogram("order_request_duration_seconds", "Time spent on order requests")

class Order(BaseModel):
    symbol: str
    side: str
    quantity: int
    price: float
    order_type: str

@app.get("/")
async def root():
    order_requests_total.inc()
    return {"message": "Order Service is running"}

@app.get("/health")
async def health():
    order_requests_total.inc()
    return {"status": "healthy"}

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")

@app.post("/api/v1/orders")
async def create_order(order: Order):
    order_requests_total.inc()
    return {"message": "Order created", "order": order}
