FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install kubectl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && chmod +x kubectl \
    && mv kubectl /usr/local/bin/

WORKDIR /app

# Copy requirements first for better caching
COPY services/backtest-request-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY services/backtest-request-service/main.py .

# Expose port
EXPOSE 8082

# Run the application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8082"] 