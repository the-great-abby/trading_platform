FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY services/market-data-worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code (needed for imports)
COPY src ./src

# Copy application code
COPY services/market-data-worker/main.py .
COPY services/market-data-worker/config.py .

# Create non-root user
RUN useradd -m -u 1000 worker && chown -R worker:worker /app
USER worker

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Expose port
EXPOSE 8080

# Run the worker
CMD ["python", "main.py"] 