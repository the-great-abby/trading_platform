# 🧠 AI IDE Integration Guide

## 🎯 **Overview**

This guide shows you how to use your local LLM (Ollama) and architecture database to create an AI-powered IDE experience with Cursor. Your setup provides:

- **Local LLM Models**: CodeLlama, Llama2, GPT-4, Claude, Mistral
- **Architecture Database**: Vectorized knowledge of your entire codebase
- **RAG Chat System**: Intelligent Q&A about your trading system
- **Context-Aware Code Assistance**: AI that understands your architecture

## 🏗️ **Your AI Infrastructure**

### **Components Available:**
1. **Ollama Service** - Local LLM models running on port 11434
2. **Architecture Vectorizer** - Scans and vectorizes your codebase
3. **PostgreSQL Vector Storage External** - Stores semantic embeddings (postgres-vector-external.postgres-infra.svc.cluster.local:5432)
4. **RAG Chat System** - Intelligent architecture Q&A

### **Models Available:**
- **gpt-oss:20b** - Best for code analysis and generation (primary model)
- **llama3.1:8b-instruct-q6_K** - Best for architecture queries and structured responses
- **CodeLlama** - Alternative for code analysis
- **Llama2** - Alternative for architecture queries
- **GPT-4** - General purpose (if available)
- **Claude** - Good for complex reasoning
- **Mistral** - Fast and efficient

## 🚀 **Quick Setup**

### **1. Run the Setup Script**
```bash
./scripts/setup-ai-ide-integration.sh
```

This will:
- Create an AI IDE service
- Deploy it to Kubernetes
- Set up port forwarding
- Create Cursor IDE configuration

### **2. Verify Setup**
```bash
# Check if AI IDE service is running
curl http://localhost:11050/api/health

# List available models
curl http://localhost:11050/api/models
```

## 🎮 **Using with Cursor IDE**

### **Method 1: Direct API Integration**

#### **Code Analysis**
```bash
curl -X POST http://localhost:11050/api/analyze-code \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def calculate_portfolio_value(positions):\n    total = 0\n    for position in positions:\n        total += position[\"quantity\"] * position[\"price\"]\n    return total",
    "file_path": "src/portfolio/calculator.py",
    "analysis_type": "optimization"
  }'
```

#### **Architecture Questions**
```bash
curl -X POST http://localhost:11050/api/query-architecture \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How does our trading system handle database connections?",
    "include_code_examples": true
  }'
```

#### **Code Generation**
```bash
curl -X POST http://localhost:11050/api/generate-code \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a function to calculate moving averages for stock data",
    "file_path": "src/indicators/moving_average.py",
    "language": "python"
  }'
```

### **Method 2: Cursor IDE Chat Integration**

#### **Ask Architecture Questions**
In Cursor's chat, ask questions like:
- "How does our trading system handle database connections?"
- "What's the architecture of our Kubernetes deployment?"
- "How do our services communicate with each other?"
- "What monitoring tools do we use?"

#### **Code-Specific Questions**
- "How should I implement error handling in our trading service?"
- "What's the best way to add a new strategy to our system?"
- "How do I debug a pod that's in CrashLoopBackOff?"

### **Method 3: Custom Cursor Extension**

Create a simple extension to integrate with your AI service:

```javascript
// cursor-ai-extension.js
const AI_IDE_URL = 'http://localhost:11050';

async function analyzeCode(code, filePath) {
    const response = await fetch(`${AI_IDE_URL}/api/analyze-code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            code: code,
            file_path: filePath,
            analysis_type: 'general'
        })
    });
    
    return await response.json();
}

async function queryArchitecture(question) {
    const response = await fetch(`${AI_IDE_URL}/api/query-architecture`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            question: question,
            include_code_examples: true
        })
    });
    
    return await response.json();
}
```

## 🎯 **Practical Examples**

### **Example 1: Code Review**
```python
# Your code
def process_trade(trade_data):
    # Process the trade
    result = calculate_profit(trade_data)
    return result

# Ask AI: "Review this function for potential improvements"
# AI Response: Based on your architecture, suggests error handling, logging, validation
```

### **Example 2: Architecture Understanding**
```
Question: "How do I add a new trading strategy to our system?"

AI Response: Based on your architecture documentation:
1. Create strategy class in src/strategies/
2. Add to strategy registry
3. Update backtest configuration
4. Add to Kubernetes deployment
5. Update monitoring dashboards
```

### **Example 3: Debugging Help**
```
Question: "My pod is in CrashLoopBackOff, how do I debug it?"

AI Response: Based on your Kubernetes setup:
1. Check pod logs: kubectl logs <pod-name> -n trading-system
2. Describe pod: kubectl describe pod <pod-name> -n trading-system
3. Check events: kubectl get events -n trading-system
4. Verify image: Check if image exists in localhost:32000
```

## 🔧 **Advanced Usage**

### **Batch Code Analysis**
```python
import requests
import os

def analyze_project():
    """Analyze entire project with AI"""
    results = []
    
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
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
                
                result = response.json()
                results.append({
                    'file': file_path,
                    'confidence': result['confidence'],
                    'suggestions': result['suggestions']
                })
    
    return results

# Run analysis
results = analyze_project()
for result in results:
    print(f"{result['file']}: {result['confidence']:.2f} confidence")
```

### **Architecture Documentation Generator**
```python
def generate_architecture_docs():
    """Generate architecture documentation using AI"""
    questions = [
        "What is the overall architecture of our trading system?",
        "How do our services communicate?",
        "What databases do we use and why?",
        "How is our system deployed in Kubernetes?",
        "What monitoring and logging do we have?"
    ]
    
    docs = []
    for question in questions:
        response = requests.post(
            'http://localhost:11050/api/query-architecture',
            json={'question': question, 'include_code_examples': True}
        )
        
        result = response.json()
        docs.append(f"## {question}\n\n{result['response']}\n")
    
    return '\n'.join(docs)

# Generate docs
architecture_docs = generate_architecture_docs()
with open('AI_GENERATED_ARCHITECTURE.md', 'w') as f:
    f.write(architecture_docs)
```

## 🎨 **Customization**

### **Model Selection**
Edit the AI IDE service configuration:

```yaml
# In k8s/ai-ide-service.yaml
env:
- name: LLM_MODEL
  value: "gpt-oss:20b"  # Primary model for code analysis and generation
- name: ARCHITECTURE_MODEL
  value: "llama3.1:8b-instruct-q6_K"  # Model for architecture queries
```

### **Custom Prompts**
Modify the prompt templates in the AI IDE service:

```python
def _build_analysis_prompt(self, request, context):
    return f"""You are an expert Python developer analyzing code for a trading system.
    
    File: {request.file_path}
    Analysis Type: {request.analysis_type}
    
    Code:
    ```python
    {request.code}
    ```
    
    Please provide specific, actionable recommendations for:
    1. Code quality improvements
    2. Performance optimizations
    3. Architecture alignment
    4. Best practices
    5. Potential bugs or issues
    
    Be specific and reference your trading system architecture."""
```

## 🚨 **Troubleshooting**

### **Service Not Responding**
```bash
# Check service status
kubectl get pods -n trading-system | grep ai-ide-service

# Check logs
kubectl logs deployment/ai-ide-service -n trading-system

# Restart service
kubectl rollout restart deployment/ai-ide-service -n trading-system
```

### **Ollama Connection Issues**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Check available models
ollama list

# Pull a model if needed
ollama pull codellama
```

### **Vector Storage Issues**
```bash
# Check external vector storage connectivity
kubectl get svc -n postgres-infra | grep postgres-vector-external

# Test vector search (from within cluster)
kubectl run test-vector --image=curlimages/curl --rm -it --restart=Never -- \
  curl -X POST http://postgres-vector-external.postgres-infra.svc.cluster.local:5432/api/vectors/search \
  -H "Content-Type: application/json" \
  -d '{"query": "kubernetes", "limit": 1}'
```

### **Architecture Vectorizer Issues**
```bash
# Check vectorizer status
kubectl get pods -n trading-system | grep architecture-vectorizer

# Run manual vectorization
kubectl create job --from=cronjob/architecture-vectorizer-job manual-vectorization -n trading-system

# Check vectorization logs
kubectl logs job/manual-vectorization -n trading-system
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

### **Trading System Specific**
- ✅ Understands your Kubernetes setup
- ✅ Knows your service architecture
- ✅ Familiar with your code patterns
- ✅ Provides relevant examples

## 🚀 **Getting Started**

1. **Run the setup script:**
   ```bash
   ./scripts/setup-ai-ide-integration.sh
   ```

2. **Test the service:**
   ```bash
   curl http://localhost:11050/api/health
   ```

3. **Start using in Cursor:**
   - Ask architecture questions in chat
   - Use API endpoints for code analysis
   - Integrate with your workflow

4. **Customize as needed:**
   - Adjust models and prompts
   - Add custom endpoints
   - Integrate with your tools

This AI IDE integration transforms your development experience by providing intelligent, context-aware assistance that truly understands your trading system architecture! 🎯
