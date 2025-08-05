FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY services/llm-worker/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared src code
COPY src /app/src

# Copy llm-worker application code
COPY services/llm-worker/main_new.py ./main.py

# Set PYTHONPATH to include /app and /app/src
ENV PYTHONPATH="/app:/app/src"

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Run the worker
CMD ["python", "main.py"] 