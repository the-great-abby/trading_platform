# LLM Proxy Service Decommissioned Rule

## Overview
The internal LLM proxy service has been decommissioned and should not be used. All LLM-related functionality should reference the external resource on port 12001.

## Current Status
- ❌ **Internal LLM Proxy Service**: Decommissioned (not running)
- ✅ **External LLM Resource**: Available on port 12001
- 🔄 **Migration Required**: Update all services to use external endpoint

## External LLM Resource
**URL**: `http://localhost:12001` (local development) or `http://host.docker.internal:12001` (Docker containers)

## Services Affected
The following services need to use the external LLM resource:

### 1. Unified Analytics Dashboard
- **File**: `services/unified-analytics-dashboard/main.py`
- **Current**: Uses `LLM_PROXY_URL` environment variable
- **Required**: Set to external resource (port 12001)

### 2. Kubernetes RAG Chat
- **File**: `services/kubernetes-rag-chat/main.py`
- **Current**: Uses `LLM_PROXY_URL` environment variable
- **Required**: Set to external resource (port 12001)

### 3. AI Stock Dashboard
- **File**: `services/ai-stock-dashboard/main.py`
- **Current**: Uses `LLM_PROXY_URL` environment variable
- **Required**: Set to external resource (port 12001)

### 4. Other AI Services
- AI Analysis Service
- AI Decision Engine
- Trading Ultra Service
- Vector Database Service

## Environment Variable Configuration

### For Local Development
```bash
export LLM_PROXY_URL=http://localhost:12001
```

### For Docker Containers
```bash
export LLM_PROXY_URL=http://host.docker.internal:12001
```

### For Kubernetes
```yaml
env:
- name: LLM_PROXY_URL
  value: "http://host.docker.internal:12001"
```

## API Endpoints
The external LLM resource provides these endpoints:

- **Generate**: `POST /api/generate`
- **Chat**: `POST /api/chat`
- **High Priority**: `POST /api/high-priority/chat`
- **Embed**: `POST /api/embed`
- **Health**: `GET /api/health`
- **Status**: `GET /api/status/{request_id}`

## Migration Steps

### 1. Update Environment Variables
```bash
# Stop using internal LLM proxy
unset LLM_PROXY_URL

# Set to external resource
export LLM_PROXY_URL=http://localhost:12001
```

### 2. Update Kubernetes Manifests
```yaml
# Remove references to internal llm-proxy service
# Update environment variables to use external endpoint
env:
- name: LLM_PROXY_URL
  value: "http://host.docker.internal:12001"
```

### 3. Remove Internal Service
```bash
# Delete the internal LLM proxy service (if it exists)
kubectl delete service llm-proxy -n trading-system
kubectl delete deployment llm-proxy -n trading-system
```

## Testing External LLM Resource

### Health Check
```bash
curl -s http://localhost:12001/api/health
```

### Test Generation
```bash
curl -X POST http://localhost:12001/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-oss:20b",
    "prompt": "Hello, how are you?",
    "stream": false
  }'
```

## Troubleshooting

### Common Issues
1. **Connection Refused**: External LLM service not running on port 12001
2. **Timeout**: External service responding slowly
3. **Authentication**: External service requires API keys

### Solutions
1. **Start External Service**: Ensure LLM service is running on port 12001
2. **Check Network**: Verify network connectivity to external service
3. **API Keys**: Configure required authentication for external service

## Code Examples

### Python Service Configuration
```python
import os

# Use external LLM resource
LLM_PROXY_URL = os.getenv("LLM_PROXY_URL", "http://localhost:12001")

# Make requests to external service
async def generate_response(prompt: str):
    async with aiohttp.ClientSession() as session:
        url = f"{LLM_PROXY_URL}/api/generate"
        # ... rest of implementation
```

### JavaScript/Node.js Configuration
```javascript
// Use external LLM resource
const LLM_PROXY_URL = process.env.LLM_PROXY_URL || 'http://localhost:12001';

// Make requests to external service
async function generateResponse(prompt) {
    const response = await fetch(`${LLM_PROXY_URL}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, model: 'gpt-oss:20b' })
    });
    return response.json();
}
```

## Compliance
- ✅ **All new services** must use external LLM resource
- ✅ **Existing services** must be migrated to external resource
- ❌ **No new services** should reference internal LLM proxy
- ❌ **No fallback** to internal LLM proxy allowed

## Monitoring
- Monitor external LLM service health on port 12001
- Track response times and error rates
- Alert on service unavailability
- Log all LLM requests for debugging

This rule ensures consistent use of the external LLM resource and prevents confusion with the decommissioned internal service.

