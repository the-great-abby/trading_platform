FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for psutil and curl
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements-minimal.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY templates/ ./templates/
COPY scripts/ ./scripts/
# COPY static/ ./static/  # Static directory doesn't exist yet

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"] 