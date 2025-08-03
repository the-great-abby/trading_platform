FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install Python dependencies
COPY services/notification-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared src code
COPY src /app/src

# Copy application code
COPY services/notification-service/main.py .

# Set PYTHONPATH to include /app and /app/src
ENV PYTHONPATH="/app:/app/src"

# Expose port
EXPOSE 8083

# Run the application
CMD ["python", "main.py"] 