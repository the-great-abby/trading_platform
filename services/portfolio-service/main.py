from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from prometheus_client import generate_latest, Counter, Histogram, Gauge
from fastapi.responses import Response

app = FastAPI(title="Portfolio Service", version="1.0.0")

# Prometheus metrics
portfolio_requests_total = Counter("portfolio_requests_total", "Total number of portfolio requests")
portfolio_request_duration = Histogram("portfolio_request_duration_seconds", "Time spent on portfolio requests")

class Portfolio(BaseModel):
    name: str
    value: float
    currency: str

@app.get("/")
async def root():
    portfolio_requests_total.inc()
    return {"message": "Portfolio Service is running"}

@app.get("/health")
async def health():
    portfolio_requests_total.inc()
    return {"status": "healthy"}

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")

@app.post("/api/v1/portfolios")
async def create_portfolio(portfolio: Portfolio):
    portfolio_requests_total.inc()
    return {"message": "Portfolio created", "portfolio": portfolio}
