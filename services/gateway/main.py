from fastapi import FastAPI
import os

app = FastAPI(title="Gateway Service", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "Gateway Service is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/v1/status")
async def get_status():
    return {
        "service": "gateway",
        "version": "1.0.0",
        "status": "operational"
    }
