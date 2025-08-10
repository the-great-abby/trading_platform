# 🎓 Kubernetes Learning Quick Start

## 🚀 Quick Commands

### 📖 Learning Guide
```bash
# View preview in terminal
make k8s-learn-preview

# Open full guide in editor
make k8s-learn
```

### 🤖 RAG Chat Service
```bash
# Deploy to Kubernetes
make k8s-rag-chat-deploy

# Start locally (if you have the service)
make k8s-rag-chat

# Port forward to access web interface
kubectl port-forward svc/kubernetes-rag-chat 11116:8000 -n trading-system
```

## 📚 What's Available

### 1. Comprehensive Learning Guide
- **Location**: `docs/KUBERNETES_LEARNING_GUIDE.md`
- **Features**: Mermaid diagrams, interactive scenarios, hands-on exercises
- **Access**: `make k8s-learn` or `make k8s-learn-preview`

### 2. AI-Powered RAG Chat
- **Location**: `services/kubernetes-rag-chat/`
- **Features**: GPT-OSS model, web interface, Kubernetes knowledge base
- **Access**: http://localhost:11116 (after port forwarding)

### 3. Interactive Learning Tools
- **Makefile Targets**: Easy access to all resources
- **Structured Path**: 8-week progressive learning program
- **Production Focus**: Real-world considerations

## 🎯 Getting Started

1. **Start with the guide preview**:
   ```bash
   make k8s-learn-preview
   ```

2. **Open the full guide**:
   ```bash
   make k8s-learn
   ```

3. **Deploy the RAG chat service**:
   ```bash
   make k8s-rag-chat-deploy
   ```

4. **Access the RAG chat**:
   ```bash
   kubectl port-forward svc/kubernetes-rag-chat 11116:8000 -n trading-system
   ```
   Then open: http://localhost:11116

## 🎮 Example Usage

### Learning Guide
- Read the comprehensive guide with Mermaid diagrams
- Follow interactive scenarios and hands-on exercises
- Use the structured 8-week learning path

### RAG Chat
Ask questions like:
- "How do I check the status of all pods?"
- "What's the difference between a pod and a deployment?"
- "How do I debug a pod that's in CrashLoopBackOff?"
- "What's the difference between Docker Desktop Kubernetes and production Kubernetes?"

## 🎯 Benefits

- **Hands-On Learning**: Uses your actual trading system
- **AI Integration**: GPT-OSS powered chat for intelligent Q&A
- **Visual Aids**: Mermaid diagrams for complex concepts
- **Production Focus**: Covers real-world scenarios
- **Structured Path**: Progressive learning program

Happy learning! 🚀