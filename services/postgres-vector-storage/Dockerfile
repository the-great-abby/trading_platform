FROM python:3.11-slim

# Add build argument to force cache invalidation
ARG CACHEBUST=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY services/postgres-vector-storage/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared src code
COPY src /app/src

# Copy application code
COPY services/postgres-vector-storage/main.py .
COPY services/postgres-vector-storage/vector_types.py .
COPY services/postgres-vector-storage/models.py .

# Set PYTHONPATH to include /app and /app/src
ENV PYTHONPATH="/app:/app/src"

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "main.py"] 