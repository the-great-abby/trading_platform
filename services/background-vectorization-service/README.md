# Background Vectorization Service

## Overview

The Background Vectorization Service automatically vectorizes new market data, news, and earnings data for RAG (Retrieval-Augmented Generation) search. This service runs continuously in the background, monitoring for new data and converting it into vector embeddings for efficient search and analysis.

## Features

### ✅ Phase 1: Service Architecture Design - COMPLETED
- Service directory structure
- FastAPI application framework
- Requirements and Dockerfile
- Kubernetes deployment manifests
- Database models and manager
- Vectorizer modules (market_data, news, earnings)

### ✅ Phase 2: Core Integration - COMPLETED
- **Vectorizer Module Integration**: All vectorizer modules integrated into main.py
- **Scheduler Components**: Automated periodic vectorization tasks
- **Job Queue Processing**: Asynchronous job processing with queue management
- **Monitoring & Metrics**: Comprehensive performance tracking and health monitoring

### ⏳ Phase 3: Deployment & Testing - PENDING
- Build and deploy to Kubernetes
- Test vectorization workflows
- Validate data processing
- Performance optimization

### ⏳ Phase 4: Production Integration - PENDING
- Hook into existing data ingestion
- Set up automated triggers
- Monitor and maintain

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Background Vectorization Service         │
├─────────────────────────────────────────────────────────────┤
│  FastAPI Application (main.py)                             │
│  ├── Health Monitoring                                     │
│  ├── Job Management                                        │
│  ├── Metrics Collection                                    │
│  └── Configuration Management                              │
├─────────────────────────────────────────────────────────────┤
│  Vectorizer Modules                                        │
│  ├── Market Data Vectorizer                                │
│  ├── News Vectorizer                                       │
│  └── Earnings Vectorizer                                   │
├─────────────────────────────────────────────────────────────┤
│  Scheduler System                                          │
│  ├── Periodic Tasks                                        │
│  ├── Job Scheduling                                        │
│  └── Task Management                                       │
├─────────────────────────────────────────────────────────────┤
│  Database Layer                                            │
│  ├── Database Manager                                      │
│  ├── Models & Schema                                       │
│  └── Connection Pooling                                    │
└─────────────────────────────────────────────────────────────┘
```

## API Endpoints

### Health & Status
- `GET /health` - Service health check with detailed status
- `GET /api/vectorization/status` - Overall vectorization service status
- `GET /api/vectorization/scheduler/status` - Scheduler status and configuration
- `GET /api/vectorization/metrics` - Service performance metrics
- `GET /api/vectorization/config` - Current service configuration

### Job Management
- `GET /api/vectorization/jobs/{job_id}` - Get status of a specific job
- `POST /api/vectorization/jobs` - Create a new vectorization job
- `POST /api/vectorization/batch` - Create multiple vectorization jobs
- `DELETE /api/vectorization/jobs/{job_id}` - Cancel a vectorization job
- `POST /api/vectorization/jobs/{job_id}/retry` - Retry a failed vectorization job

### Operations
- `POST /api/vectorization/trigger` - Manually trigger vectorization of all available data
- `POST /api/vectorization/cleanup` - Clean up old completed and failed jobs

### Documentation
- `GET /api/docs` - Comprehensive API documentation

## Data Types Supported

### 1. Market Data
- Price movements and trends
- Volume analysis
- Technical indicators
- Market sentiment analysis
- Support/resistance levels

### 2. News Data
- Financial news articles
- Sentiment analysis
- Entity extraction
- Topic classification
- Relevance scoring

### 3. Earnings Data
- Quarterly earnings reports
- Revenue and EPS data
- Surprise analysis
- Historical comparisons
- Forward-looking statements

## Configuration

The service can be configured using environment variables:

```bash
# Vectorization Settings
VECTORIZATION_BATCH_SIZE=10
VECTORIZATION_MAX_RETRIES=3
VECTORIZATION_RETRY_DELAY=60

# Scheduling Intervals (in seconds)
MARKET_DATA_INTERVAL=3600    # 1 hour
NEWS_INTERVAL=1800          # 30 minutes
EARNINGS_INTERVAL=7200      # 2 hours

# Service URLs
VECTOR_STORAGE_URL=http://postgres-vector-storage:80
LLM_PROXY_URL=http://llm-proxy:12001
DATABASE_URL=postgresql://user:pass@host:port/db

# Feature Flags
ENABLE_AUTO_VECTORIZATION=true
```

## Job Processing

### Job Lifecycle
1. **Pending**: Job created and queued
2. **Processing**: Job being processed by vectorizer
3. **Completed**: Vectorization successful
4. **Failed**: Vectorization failed (can be retried)
5. **Cancelled**: Job cancelled by user

### Progress Tracking
- Real-time progress updates (0.0 to 1.0)
- Processing time tracking
- Success/failure metrics
- Retry count monitoring

### Queue Management
- Priority-based job ordering
- Batch job creation
- Automatic cleanup of old jobs
- Queue size monitoring

## Monitoring & Metrics

### Performance Metrics
- Total jobs processed
- Successful vectorizations
- Failed vectorizations
- Average processing time
- Queue size and throughput

### Health Monitoring
- Service uptime
- Database connectivity
- Vectorizer status
- Scheduler status
- Resource utilization

### Logging
- Structured logging with different levels
- Job-specific logging
- Error tracking and reporting
- Performance monitoring

## Deployment

### Docker
```bash
# Build image
docker build -t background-vectorization-service .

# Run container
docker run -p 8080:8080 background-vectorization-service
```

### Kubernetes
```bash
# Deploy to cluster
kubectl apply -f k8s-deployment-fixed.yaml

# Check status
kubectl get pods -n trading-system -l app=background-vectorization-service
```

## Development

### Prerequisites
- Python 3.8+
- FastAPI
- asyncpg
- aiohttp
- pydantic

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run service
python main.py

# Run with hot reload
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

### Testing
```bash
# Health check
curl http://localhost:8080/health

# Get metrics
curl http://localhost:8080/api/vectorization/metrics

# Create test job
curl -X POST http://localhost:8080/api/vectorization/jobs \
  -H "Content-Type: application/json" \
  -d '{"job_id": "test_001", "data_type": "market_data", "symbol": "AAPL", "data": {}}'
```

## Next Steps

### Phase 3: Deployment & Testing
1. Build Docker image and deploy to Kubernetes
2. Test vectorization workflows end-to-end
3. Validate data processing accuracy
4. Performance testing and optimization

### Phase 4: Production Integration
1. Connect to existing data ingestion pipelines
2. Set up automated triggers and monitoring
3. Production deployment and maintenance
4. Performance tuning and scaling

## Troubleshooting

### Common Issues
1. **Import Errors**: Check relative import paths in vectorizer modules
2. **Database Connection**: Verify DATABASE_URL and network connectivity
3. **Vector Storage**: Ensure postgres-vector-storage service is running
4. **Scheduler Issues**: Check scheduler status and task logs

### Debug Commands
```bash
# Check service health
curl http://localhost:8080/health

# View scheduler status
curl http://localhost:8080/api/vectorization/scheduler/status

# Check job queue
curl http://localhost:8080/api/vectorization/status

# View configuration
curl http://localhost:8080/api/vectorization/config
```

## Contributing

When adding new features or modifying existing code:

1. Update the README.md with new endpoints/features
2. Add appropriate logging and error handling
3. Update configuration options if needed
4. Test thoroughly before committing
5. Update the Makefile.simple progress tracking

## License

This service is part of the Trading System project and follows the same licensing terms.

