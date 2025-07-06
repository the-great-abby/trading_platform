from fastapi import FastAPI
import os

app = FastAPI(title="Command Api Service", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "Command Api Service is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/v1/status")
async def get_status():
    return {
        "service": "command-api",
        "version": "1.0.0",
        "status": "operational"
    }
