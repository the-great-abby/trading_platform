FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install Python dependencies
COPY services/report-viewer-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared src code
COPY src /app/src

# Copy application code
COPY services/report-viewer-service/main.py .

# Set PYTHONPATH to include /app and /app/src
ENV PYTHONPATH="/app:/app/src"

# Expose port
EXPOSE 8084

# Run the application
CMD ["python", "main.py"] 