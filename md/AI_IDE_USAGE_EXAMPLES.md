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
