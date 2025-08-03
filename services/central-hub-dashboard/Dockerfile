FROM python:3.11-slim

WORKDIR /app

COPY services/central-hub-dashboard/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/central-hub-dashboard/main.py .
COPY services/central-hub-dashboard/templates/ ./templates/
COPY src/ ./src/

EXPOSE 8000

CMD ["python", "main.py"] 