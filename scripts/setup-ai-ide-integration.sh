#!/bin/bash

# 🧠 AI IDE Integration Setup
# This script sets up your local LLM and architecture database for Cursor IDE integration

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🧠 AI IDE Integration Setup${NC}"
echo "=================================="
echo ""

# Function to print section headers
print_section() {
    echo -e "\n${BLUE}$1${NC}"
    echo "----------------------------------------"
}

# Function to wait for user input
wait_for_user() {
    echo -e "\n${GREEN}Press Enter to continue...${NC}"
    read -r
}

# Check prerequisites
check_prerequisites() {
    print_section "Checking Prerequisites"
    
    echo "Checking if Ollama is running..."
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Ollama is running${NC}"
        echo "Available models:"
        curl -s http://localhost:11434/api/tags | jq -r '.models[].name' 2>/dev/null || echo "  (jq not available, but Ollama is running)"
    else
        echo -e "${RED}❌ Ollama is not running${NC}"
        echo "Please start Ollama first:"
        echo "  ollama serve"
        exit 1
    fi
    
    echo ""
    echo "Checking if architecture vectorizer is running..."
    if kubectl get pods -n trading-system | grep architecture-vectorizer | grep Running > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Architecture vectorizer is running${NC}"
    else
        echo -e "${YELLOW}⚠️  Architecture vectorizer is not running${NC}"
        echo "Starting architecture vectorizer..."
        kubectl apply -f k8s/architecture-vectorizer.yaml
        sleep 10
    fi
    
    echo ""
    echo "Checking if postgres-vector-storage service is running..."
    if kubectl get svc -n trading-system | grep postgres-vector-storage > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Postgres vector storage service is available${NC}"
        
        # Test connectivity to vector storage service
        echo "Testing connectivity to vector storage service..."
        if kubectl run test-vector-connectivity --image=curlimages/curl --rm -it --restart=Never --timeout=10s -- \
           curl -s -f http://postgres-vector-storage:80/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Vector storage service is accessible${NC}"
        else
            echo -e "${YELLOW}⚠️  Vector storage service exists but may not be fully ready${NC}"
            echo "This is normal if the service is still starting up"
        fi
    else
        echo -e "${RED}❌ Postgres vector storage service not found${NC}"
        echo "Please ensure the postgres-vector-storage service is deployed in trading-system namespace"
        echo "Expected service: postgres-vector-storage:80"
        exit 1
    fi
}

# Create AI IDE service
create_ai_ide_service() {
    print_section "Creating AI IDE Service"
    
    echo "Creating AI IDE service directory..."
    mkdir -p services/ai-ide-service
    
    cat > services/ai-ide-service/main.py << 'EOF'
#!/usr/bin/env python3
"""
AI IDE Service - Bridge between Cursor IDE and your local AI infrastructure
Provides intelligent code assistance using your architecture database and local LLM
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import aiohttp
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import hashlib
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI IDE Service", version="1.0.0")

# Add CORS middleware for Cursor IDE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to Cursor IDE
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
VECTOR_STORAGE_URL = os.getenv("VECTOR_STORAGE_URL", "http://postgres-vector-storage:80")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-oss:20b")  # Best for code analysis and generation
ARCHITECTURE_MODEL = os.getenv("ARCHITECTURE_MODEL", "llama3.1:8b-instruct-q6_K")  # Best for architecture queries

class CodeAnalysisRequest(BaseModel):
    code: str
    file_path: str
    context: Optional[str] = None
    analysis_type: str = "general"  # general, bug_fix, optimization, documentation

class ArchitectureQueryRequest(BaseModel):
    question: str
    context: Optional[str] = None
    include_code_examples: bool = True

class CodeGenerationRequest(BaseModel):
    prompt: str
    file_path: str
    existing_code: Optional[str] = None
    language: str = "python"

class AIIDEResponse(BaseModel):
    response: str
    confidence: float
    sources: List[Dict[str, Any]]
    suggestions: List[str]
    timestamp: datetime

class AIIDEService:
    """AI IDE Service for intelligent code assistance"""
    
    def __init__(self):
        self.ollama_url = OLLAMA_URL
        self.vector_storage_url = VECTOR_STORAGE_URL
        self.llm_model = LLM_MODEL
        self.architecture_model = ARCHITECTURE_MODEL
        
        # Cache for frequently accessed information
        self.code_cache = {}
        self.architecture_cache = {}
        
        logger.info(f"AI IDE Service initialized with Ollama at {self.ollama_url}")
    
    async def analyze_code(self, request: CodeAnalysisRequest) -> AIIDEResponse:
        """Analyze code using architecture context and local LLM"""
        try:
            # Search architecture database for relevant context
            architecture_context = await self._search_architecture_context(
                request.code, request.file_path
            )
            
            # Prepare analysis prompt
            prompt = self._build_analysis_prompt(request, architecture_context)
            
            # Get LLM analysis
            llm_response = await self._query_ollama(prompt, self.llm_model)
            
            # Extract suggestions and confidence
            suggestions = self._extract_suggestions(llm_response)
            confidence = self._calculate_confidence(llm_response, architecture_context)
            
            return AIIDEResponse(
                response=llm_response,
                confidence=confidence,
                sources=architecture_context,
                suggestions=suggestions,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Code analysis failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def query_architecture(self, request: ArchitectureQueryRequest) -> AIIDEResponse:
        """Query architecture database for intelligent responses"""
        try:
            # Search vector storage
            search_results = await self._search_vector_storage(request.question)
            
            # Build context-aware prompt
            prompt = self._build_architecture_prompt(request, search_results)
            
            # Get LLM response
            llm_response = await self._query_ollama(prompt, self.architecture_model)
            
            return AIIDEResponse(
                response=llm_response,
                confidence=0.9,  # High confidence for architecture queries
                sources=search_results,
                suggestions=self._extract_architecture_suggestions(search_results),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Architecture query failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def generate_code(self, request: CodeGenerationRequest) -> AIIDEResponse:
        """Generate code using architecture context"""
        try:
            # Search for similar code patterns
            similar_code = await self._search_similar_code(request.prompt, request.file_path)
            
            # Build generation prompt
            prompt = self._build_generation_prompt(request, similar_code)
            
            # Generate code
            generated_code = await self._query_ollama(prompt, self.llm_model)
            
            return AIIDEResponse(
                response=generated_code,
                confidence=0.8,
                sources=similar_code,
                suggestions=self._extract_code_suggestions(generated_code),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _search_architecture_context(self, code: str, file_path: str) -> List[Dict[str, Any]]:
        """Search architecture database for relevant context"""
        try:
            # Extract key concepts from code
            concepts = self._extract_code_concepts(code, file_path)
            
            # Search vector storage
            search_query = f"{' '.join(concepts)} {file_path}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.vector_storage_url}/api/vectors/search",
                    json={
                        "query": search_query,
                        "limit": 5,
                        "namespace": "architecture_*"
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("results", [])
                    else:
                        logger.warning(f"Vector search failed: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Architecture context search failed: {e}")
            return []
    
    async def _search_vector_storage(self, query: str) -> List[Dict[str, Any]]:
        """Search vector storage for relevant information"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.vector_storage_url}/api/vectors/search",
                    json={
                        "query": query,
                        "limit": 10,
                        "namespace": "architecture_*"
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("results", [])
                    else:
                        logger.warning(f"Vector search failed: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Vector storage search failed: {e}")
            return []
    
    async def _query_ollama(self, prompt: str, model: str) -> str:
        """Query Ollama for LLM response"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "top_p": 0.9,
                            "max_tokens": 2000
                        }
                    },
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("response", "")
                    else:
                        logger.error(f"Ollama query failed: {response.status}")
                        return "Error: Could not generate response"
                        
        except Exception as e:
            logger.error(f"Ollama query failed: {e}")
            return "Error: Could not connect to Ollama"
    
    def _extract_code_concepts(self, code: str, file_path: str) -> List[str]:
        """Extract key concepts from code for context search"""
        concepts = []
        
        # Extract from file path
        if "k8s" in file_path:
            concepts.append("kubernetes")
        if "service" in file_path:
            concepts.append("service")
        if "trading" in file_path:
            concepts.append("trading")
        
        # Extract from code content
        if "class " in code:
            concepts.append("class")
        if "def " in code:
            concepts.append("function")
        if "import " in code:
            concepts.append("import")
        if "async" in code:
            concepts.append("async")
        
        return concepts
    
    def _build_analysis_prompt(self, request: CodeAnalysisRequest, context: List[Dict[str, Any]]) -> str:
        """Build analysis prompt with architecture context"""
        context_str = ""
        if context:
            context_str = "\n\nRelevant Architecture Context:\n"
            for item in context[:3]:  # Limit to top 3 results
                context_str += f"- {item.get('content', '')[:200]}...\n"
        
        return f"""Analyze the following code and provide intelligent suggestions:

File: {request.file_path}
Analysis Type: {request.analysis_type}

Code:
```python
{request.code}
```

{context_str}

Please provide:
1. Code quality assessment
2. Potential improvements
3. Architecture alignment
4. Best practices suggestions
5. Potential issues or bugs

Be specific and actionable in your recommendations."""

    def _build_architecture_prompt(self, request: ArchitectureQueryRequest, context: List[Dict[str, Any]]) -> str:
        """Build architecture query prompt"""
        context_str = ""
        if context:
            context_str = "\n\nRelevant Documentation:\n"
            for item in context[:5]:
                context_str += f"- {item.get('content', '')[:300]}...\n"
        
        return f"""Answer the following question about our trading system architecture:

Question: {request.question}

{context_str}

Please provide a comprehensive answer based on our actual architecture documentation. Include specific examples and references where possible."""

    def _build_generation_prompt(self, request: CodeGenerationRequest, similar_code: List[Dict[str, Any]]) -> str:
        """Build code generation prompt"""
        similar_str = ""
        if similar_code:
            similar_str = "\n\nSimilar Code Patterns:\n"
            for item in similar_code[:2]:
                similar_str += f"```python\n{item.get('content', '')[:500]}...\n```\n"
        
        return f"""Generate code for the following request:

Prompt: {request.prompt}
File: {request.file_path}
Language: {request.language}

{similar_str}

Please generate clean, well-documented code that follows our architecture patterns."""

    def _extract_suggestions(self, response: str) -> List[str]:
        """Extract actionable suggestions from LLM response"""
        suggestions = []
        lines = response.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['suggest', 'recommend', 'consider', 'should']):
                suggestions.append(line.strip())
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def _extract_architecture_suggestions(self, sources: List[Dict[str, Any]]) -> List[str]:
        """Extract architecture-related suggestions"""
        suggestions = []
        for source in sources:
            if 'file_path' in source:
                suggestions.append(f"Review: {source['file_path']}")
        return suggestions[:3]
    
    def _extract_code_suggestions(self, code: str) -> List[str]:
        """Extract code-related suggestions"""
        suggestions = []
        if "TODO" in code:
            suggestions.append("Complete TODO items")
        if "FIXME" in code:
            suggestions.append("Address FIXME comments")
        if "import" in code:
            suggestions.append("Verify all imports are used")
        return suggestions
    
    def _calculate_confidence(self, response: str, context: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on response quality and context"""
        base_confidence = 0.5
        
        # Boost confidence if we have good context
        if context:
            base_confidence += 0.3
        
        # Boost confidence if response is detailed
        if len(response) > 200:
            base_confidence += 0.2
        
        return min(base_confidence, 1.0)

# Initialize service
ai_ide_service = AIIDEService()

@app.post("/api/analyze-code", response_model=AIIDEResponse)
async def analyze_code(request: CodeAnalysisRequest):
    """Analyze code with architecture context"""
    return await ai_ide_service.analyze_code(request)

@app.post("/api/query-architecture", response_model=AIIDEResponse)
async def query_architecture(request: ArchitectureQueryRequest):
    """Query architecture database"""
    return await ai_ide_service.query_architecture(request)

@app.post("/api/generate-code", response_model=AIIDEResponse)
async def generate_code(request: CodeGenerationRequest):
    """Generate code with architecture context"""
    return await ai_ide_service.generate_code(request)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "ollama_url": OLLAMA_URL,
        "vector_storage_url": VECTOR_STORAGE_URL,
        "models": {
            "llm_model": LLM_MODEL,
            "architecture_model": ARCHITECTURE_MODEL
        }
    }

@app.get("/api/models")
async def list_models():
    """List available Ollama models"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.ollama_url}/api/tags") as response:
                if response.status == 200:
                    result = await response.json()
                    return {"models": [model["name"] for model in result.get("models", [])]}
                else:
                    return {"error": "Could not fetch models"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=11050)
EOF

    echo "Creating requirements.txt..."
    cat > services/ai-ide-service/requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn==0.24.0
aiohttp==3.9.1
pydantic==2.5.0
python-multipart==0.0.6
EOF

    echo "Creating Dockerfile..."
    cat > services/ai-ide-service/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

EXPOSE 11050

CMD ["python", "main.py"]
EOF

    echo -e "${GREEN}✅ AI IDE service created${NC}"
}

# Create Kubernetes deployment
create_k8s_deployment() {
    print_section "Creating Kubernetes Deployment"
    
    cat > k8s/ai-ide-service.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-ide-service
  namespace: trading-system
  labels:
    app: ai-ide-service
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ai-ide-service
  template:
    metadata:
      labels:
        app: ai-ide-service
    spec:
      containers:
      - name: ai-ide-service
        image: localhost:32000/ai-ide-service:latest
        ports:
        - containerPort: 11050
        env:
        - name: OLLAMA_URL
          value: "http://host.docker.internal:11434"
        - name: VECTOR_STORAGE_URL
          value: "http://postgres-vector-storage:80"
        - name: LLM_MODEL
          value: "gpt-oss:20b"
        - name: ARCHITECTURE_MODEL
          value: "llama3.1:8b-instruct-q6_K"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 11050
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health
            port: 11050
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: ai-ide-service
  namespace: trading-system
  labels:
    app: ai-ide-service
spec:
  type: ClusterIP
  ports:
  - port: 11050
    targetPort: 11050
    protocol: TCP
  selector:
    app: ai-ide-service
EOF

    echo -e "${GREEN}✅ Kubernetes deployment created${NC}"
}

# Create Cursor IDE configuration
create_cursor_config() {
    print_section "Creating Cursor IDE Configuration"
    
    echo "Creating Cursor IDE configuration..."
    mkdir -p .cursor
    
    cat > .cursor/ai-ide-config.json << 'EOF'
{
  "ai_ide_service": {
    "base_url": "http://localhost:11050",
    "endpoints": {
      "analyze_code": "/api/analyze-code",
      "query_architecture": "/api/query-architecture",
      "generate_code": "/api/generate-code",
      "health": "/api/health",
      "models": "/api/models"
    },
    "models": {
      "code_analysis": "gpt-oss:20b",
      "architecture": "llama3.1:8b-instruct-q6_K",
      "general": "gpt-oss:20b"
    },
    "settings": {
      "auto_analyze": true,
      "include_architecture_context": true,
      "confidence_threshold": 0.7,
      "max_suggestions": 5
    }
  }
}
EOF

    echo "Creating Cursor IDE extension configuration..."
    cat > .cursor/extension-config.json << 'EOF'
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-kubernetes-tools.vscode-kubernetes-tools",
    "redhat.vscode-yaml",
    "ms-vscode.vscode-json"
  ],
  "settings": {
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.analysis.extraPaths": [
      "./src",
      "./services"
    ],
    "files.associations": {
      "*.yaml": "yaml",
      "*.yml": "yaml",
      "Makefile*": "makefile"
    },
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
EOF

    echo -e "${GREEN}✅ Cursor IDE configuration created${NC}"
}

# Create usage examples
create_usage_examples() {
    print_section "Creating Usage Examples"
    
    cat > AI_IDE_USAGE_EXAMPLES.md << 'EOF'
# 🧠 AI IDE Usage Examples

## 🚀 **Getting Started**

### **1. Start the AI IDE Service**
```bash
# Build and deploy
cd services/ai-ide-service
docker build -t localhost:32000/ai-ide-service:latest .
docker push localhost:32000/ai-ide-service:latest

# Deploy to Kubernetes
kubectl apply -f k8s/ai-ide-service.yaml

# Port forward for local access
kubectl port-forward service/ai-ide-service 11050:11050 -n trading-system
```

### **2. Test the Service**
```bash
# Health check
curl http://localhost:11050/api/health

# List available models
curl http://localhost:11050/api/models
```

## 🎯 **Usage Examples**

### **Code Analysis**
```bash
curl -X POST http://localhost:11050/api/analyze-code \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def calculate_portfolio_value(positions):\n    total = 0\n    for position in positions:\n        total += position[\"quantity\"] * position[\"price\"]\n    return total",
    "file_path": "src/portfolio/calculator.py",
    "analysis_type": "optimization"
  }'
```

### **Architecture Queries**
```bash
curl -X POST http://localhost:11050/api/query-architecture \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How does our trading system handle database connections?",
    "include_code_examples": true
  }'
```

### **Code Generation**
```bash
curl -X POST http://localhost:11050/api/generate-code \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a function to calculate moving averages for stock data",
    "file_path": "src/indicators/moving_average.py",
    "language": "python"
  }'
```

## 🔧 **Cursor IDE Integration**

### **Manual Integration**
1. **Open Cursor IDE**
2. **Go to Settings** → **Extensions** → **AI**
3. **Add Custom AI Service**:
   - URL: `http://localhost:11050`
   - API Key: (leave empty for local service)

### **Using the AI IDE Service**
1. **Code Analysis**: Right-click on code → "Analyze with AI"
2. **Architecture Questions**: Use Cursor's chat with context
3. **Code Generation**: Ask for code generation with architecture context

## 🎮 **Advanced Usage**

### **Batch Code Analysis**
```python
import requests
import json

def analyze_file(file_path):
    with open(file_path, 'r') as f:
        code = f.read()
    
    response = requests.post(
        'http://localhost:11050/api/analyze-code',
        json={
            'code': code,
            'file_path': file_path,
            'analysis_type': 'general'
        }
    )
    
    return response.json()

# Analyze multiple files
files = ['src/trading/strategy.py', 'src/portfolio/manager.py']
for file in files:
    result = analyze_file(file)
    print(f"Analysis for {file}: {result['confidence']:.2f} confidence")
```

### **Architecture Documentation**
```python
def query_architecture(question):
    response = requests.post(
        'http://localhost:11050/api/query-architecture',
        json={
            'question': question,
            'include_code_examples': True
        }
    )
    
    return response.json()

# Ask about system architecture
result = query_architecture("How do our services communicate with each other?")
print(result['response'])
```

## 🎯 **Best Practices**

### **1. Use Specific File Paths**
- Always include the full file path for better context
- Use relative paths from project root

### **2. Provide Context**
- Include relevant context in your requests
- Mention the purpose of the code

### **3. Iterative Improvement**
- Use the AI suggestions as starting points
- Refine based on your specific needs

### **4. Architecture Awareness**
- Ask architecture questions before major changes
- Use the vector database for context

## 🚨 **Troubleshooting**

### **Service Not Responding**
```bash
# Check service status
kubectl get pods -n trading-system | grep ai-ide-service

# Check logs
kubectl logs deployment/ai-ide-service -n trading-system

# Check port forwarding
kubectl port-forward service/ai-ide-service 11050:11050 -n trading-system
```

### **Ollama Connection Issues**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Check available models
curl http://localhost:11434/api/tags | jq '.models[].name'
```

### **Vector Storage Issues**
```bash
# Check external vector storage service
kubectl get svc -n postgres-infra | grep postgres-vector-external

# Test vector search (from within cluster)
kubectl run test-vector --image=curlimages/curl --rm -it --restart=Never -- \
  curl -X POST http://postgres-vector-external.postgres-infra.svc.cluster.local:5432/api/vectors/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "limit": 1}'
```

## 🎉 **Benefits**

### **Intelligent Code Assistance**
- ✅ Context-aware code analysis
- ✅ Architecture-aligned suggestions
- ✅ Best practices recommendations
- ✅ Bug detection and prevention

### **Architecture Understanding**
- ✅ Deep knowledge of your system
- ✅ Service relationship awareness
- ✅ Pattern recognition
- ✅ Documentation integration

### **Local and Private**
- ✅ No data sent to external services
- ✅ Full control over your code
- ✅ Customizable models
- ✅ Offline capability

This AI IDE integration transforms your development experience by providing intelligent, context-aware assistance that truly understands your trading system architecture! 🚀
EOF

    echo -e "${GREEN}✅ Usage examples created${NC}"
}

# Build and deploy
build_and_deploy() {
    print_section "Building and Deploying AI IDE Service"
    
    echo "Building Docker image..."
    cd services/ai-ide-service
    docker build -t localhost:32000/ai-ide-service:latest .
    docker push localhost:32000/ai-ide-service:latest
    cd ../..
    
    echo "Deploying to Kubernetes..."
    kubectl apply -f k8s/ai-ide-service.yaml
    
    echo "Waiting for deployment..."
    kubectl wait --for=condition=available --timeout=300s deployment/ai-ide-service -n trading-system
    
    echo "Setting up port forwarding..."
    kubectl port-forward service/ai-ide-service 11050:11050 -n trading-system &
    PORT_FORWARD_PID=$!
    
    echo "Waiting for service to be ready..."
    sleep 10
    
    echo "Testing service..."
    if curl -s http://localhost:11050/api/health > /dev/null; then
        echo -e "${GREEN}✅ AI IDE service is running${NC}"
        echo "Service URL: http://localhost:11050"
        echo "Port forward PID: $PORT_FORWARD_PID"
    else
        echo -e "${RED}❌ Service is not responding${NC}"
        echo "Check logs: kubectl logs deployment/ai-ide-service -n trading-system"
    fi
}

# Main execution
main() {
    check_prerequisites
    wait_for_user
    
    create_ai_ide_service
    wait_for_user
    
    create_k8s_deployment
    wait_for_user
    
    create_cursor_config
    wait_for_user
    
    create_usage_examples
    wait_for_user
    
    build_and_deploy
    
    echo -e "\n${GREEN}🎉 AI IDE Integration Setup Complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Open Cursor IDE"
    echo "2. Configure AI service: http://localhost:11050"
    echo "3. Start using intelligent code assistance"
    echo "4. Read AI_IDE_USAGE_EXAMPLES.md for detailed usage"
    echo ""
    echo "Service is running at: http://localhost:11050"
    echo "Port forward PID: $PORT_FORWARD_PID"
}

# Run main function
main
