FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY services/data-pipeline-dashboard/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY services/data-pipeline-dashboard/main.py .
COPY services/data-pipeline-dashboard/templates ./templates

# Copy source code
COPY src ./src

# Expose port
EXPOSE 11137

# Run the application
CMD ["python", "main.py"] 