#!/usr/bin/env python3
import os

services = [
    'gateway', 'command-api', 'query-api', 'trading-service', 
    'market-data-service', 'portfolio-service', 'risk-service', 
    'strategy-service', 'order-service', 'analytics-service', 'user-service'
]

for service in services:
    service_dir = f"services/{service}"
    
    # Create Dockerfile
    dockerfile_content = f"""FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
    
    with open(f"{service_dir}/Dockerfile", "w") as f:
        f.write(dockerfile_content)
    
    # Create requirements.txt
    requirements_content = """fastapi==0.104.1
uvicorn==0.24.0
requests==2.31.0
python-dotenv==1.0.0
"""
    
    with open(f"{service_dir}/requirements.txt", "w") as f:
        f.write(requirements_content)
    
    # Create main.py
    main_content = f"""from fastapi import FastAPI
import os

app = FastAPI(title="{service.replace('-', ' ').title()} Service", version="1.0.0")

@app.get("/")
async def root():
    return {{"message": "{service.replace('-', ' ').title()} Service is running"}}

@app.get("/health")
async def health():
    return {{"status": "healthy"}}

@app.get("/api/v1/status")
async def get_status():
    return {{
        "service": "{service}",
        "version": "1.0.0",
        "status": "operational"
    }}
"""
    
    with open(f"{service_dir}/main.py", "w") as f:
        f.write(main_content)

print("All service files created successfully!") 