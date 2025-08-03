FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY services/data-analysis-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY services/data-analysis-service/main.py .

# Copy source code
COPY src ./src

# Expose port
EXPOSE 11136

# Run the application
CMD ["python", "main.py"] 