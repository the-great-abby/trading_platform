# 🤖 AI Model Selection Guide

## 🎯 **Model Configuration**

Your AI IDE integration is configured to use the following models based on their strengths:

### **Primary Models:**

1. **gpt-oss:20b** - Code Analysis & Generation
   - **Use Case**: Code analysis, code generation, optimization suggestions
   - **Strengths**: Excellent code understanding, good at generating clean code
   - **Best For**: Code review, refactoring suggestions, implementation help

2. **llama3.1:8b-instruct-q6_K** - Architecture Queries
   - **Use Case**: Architecture questions, documentation queries, structured responses
   - **Strengths**: Good at following instructions, structured output, architecture understanding
   - **Best For**: System design questions, documentation generation, structured explanations

## 🔧 **Configuration Details**

### **Environment Variables:**
```bash
LLM_MODEL=gpt-oss:20b                    # For code analysis and generation
ARCHITECTURE_MODEL=llama3.1:8b-instruct-q6_K  # For architecture queries
```

### **Kubernetes Configuration:**
```yaml
env:
- name: LLM_MODEL
  value: "gpt-oss:20b"
- name: ARCHITECTURE_MODEL
  value: "llama3.1:8b-instruct-q6_K"
```

## 🎮 **Usage Examples**

### **Code Analysis (gpt-oss:20b)**
```bash
curl -X POST http://localhost:11050/api/analyze-code \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def calculate_portfolio_value(positions):\n    total = 0\n    for position in positions:\n        total += position[\"quantity\"] * position[\"price\"]\n    return total",
    "file_path": "src/portfolio/calculator.py",
    "analysis_type": "optimization"
  }'
```

### **Architecture Queries (llama3.1:8b-instruct-q6_K)**
```bash
curl -X POST http://localhost:11050/api/query-architecture \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How does our trading system handle database connections?",
    "include_code_examples": true
  }'
```

### **Code Generation (gpt-oss:20b)**
```bash
curl -X POST http://localhost:11050/api/generate-code \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a function to calculate moving averages for stock data",
    "file_path": "src/indicators/moving_average.py",
    "language": "python"
  }'
```

## 🔄 **Model Selection Logic**

### **Automatic Model Selection:**
- **Code Analysis**: Always uses `gpt-oss:20b`
- **Architecture Queries**: Always uses `llama3.1:8b-instruct-q6_K`
- **Code Generation**: Always uses `gpt-oss:20b`

### **Why These Models?**

#### **gpt-oss:20b for Code Tasks:**
- ✅ Excellent code understanding and generation
- ✅ Good at following coding best practices
- ✅ Strong performance on code analysis tasks
- ✅ Reliable for generating clean, functional code

#### **llama3.1:8b-instruct-q6_K for Architecture:**
- ✅ Excellent at following structured instructions
- ✅ Good at providing organized, comprehensive responses
- ✅ Strong performance on documentation and explanation tasks
- ✅ Reliable for generating structured, readable content

## 🎨 **Customization Options**

### **Change Models:**
Edit the environment variables in `k8s/ai-ide-service.yaml`:

```yaml
env:
- name: LLM_MODEL
  value: "your-preferred-code-model"  # e.g., "codellama", "gpt-4"
- name: ARCHITECTURE_MODEL
  value: "your-preferred-arch-model"  # e.g., "llama2", "claude"
```

### **Available Alternatives:**
- **Code Models**: `codellama`, `gpt-4`, `claude`, `mistral`
- **Architecture Models**: `llama2`, `gpt-4`, `claude`, `mistral`

## 🚀 **Performance Considerations**

### **Model Performance:**
- **gpt-oss:20b**: ~2-5 seconds response time for code analysis
- **llama3.1:8b-instruct-q6_K**: ~1-3 seconds response time for architecture queries

### **Resource Usage:**
- **Memory**: ~4-8GB per model (depending on quantization)
- **CPU**: Moderate usage during inference
- **Storage**: ~10-20GB per model

## 🔍 **Model Verification**

### **Check Available Models:**
```bash
# List all available models in Ollama
ollama list

# Test specific model
ollama run gpt-oss:20b "Hello, can you analyze code?"
ollama run llama3.1:8b-instruct-q6_K "Hello, can you explain architecture?"
```

### **Verify Model Configuration:**
```bash
# Check AI IDE service health
curl http://localhost:11050/api/health

# List models used by AI IDE service
curl http://localhost:11050/api/models
```

## 🎯 **Best Practices**

### **For Code Analysis:**
- Use specific file paths for better context
- Include relevant code snippets
- Specify analysis type (optimization, bug_fix, etc.)

### **For Architecture Queries:**
- Ask specific, focused questions
- Request code examples when needed
- Use structured questions for better responses

### **For Code Generation:**
- Provide clear, specific prompts
- Include file path for context
- Specify language and requirements

## 🚨 **Troubleshooting**

### **Model Not Found:**
```bash
# Pull the required models
ollama pull gpt-oss:20b
ollama pull llama3.1:8b-instruct-q6_K
```

### **Model Performance Issues:**
- Check available system resources
- Consider using quantized versions
- Monitor model response times

### **Model Configuration Issues:**
- Verify environment variables
- Check Kubernetes deployment
- Restart AI IDE service if needed

## 🎉 **Benefits of This Configuration**

### **Optimized Performance:**
- ✅ Right model for each task type
- ✅ Faster response times
- ✅ Better quality responses

### **Cost Effective:**
- ✅ Local models (no API costs)
- ✅ Efficient resource usage
- ✅ No external dependencies

### **Privacy & Security:**
- ✅ All processing happens locally
- ✅ No data sent to external services
- ✅ Full control over your code

This model configuration provides the best balance of performance, quality, and efficiency for your AI IDE integration! 🚀
