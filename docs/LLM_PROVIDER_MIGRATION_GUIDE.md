# 🔄 LLM Provider Migration Guide: Ollama → LM Studio

**Last Updated**: December 4, 2025  
**Status**: ✅ Provider abstraction layer complete  
**Goal**: Support both Ollama and LM Studio (and other providers) with easy configuration

---

## 🎯 Overview

Your trading system now supports **multiple LLM providers** through a unified abstraction layer!

### Supported Providers

| Provider | Status | Use Case | Cost |
|----------|--------|----------|------|
| **Ollama** | ✅ Supported | Self-hosted, local inference | Free |
| **LM Studio** | ✅ Supported | Local GUI, easier model management | Free |
| **OpenAI** | ✅ Supported | Cloud API, most capable | Paid |
| **Custom** | 🔧 Extensible | Roll your own | Varies |

---

## 🏗️ Architecture

### Before (Ollama Only)

```
Trading Services → OllamaService → Ollama API
```

### After (Multi-Provider)

```
Trading Services → LLMProviderFactory
                    ├── OllamaProvider → Ollama API
                    ├── LMStudioProvider → LM Studio API (OpenAI-compatible)
                    └── OpenAIProvider → OpenAI API
```

### Key Components

```
src/services/llm_providers/
├── __init__.py              # Package exports
├── base.py                  # Abstract provider interface
├── factory.py               # Provider factory
├── ollama_provider.py       # Ollama implementation
├── lmstudio_provider.py     # LM Studio implementation
└── openai_provider.py       # OpenAI implementation
```

---

## 🚀 Quick Start

### Option 1: Switch to LM Studio (Environment Variable)

**Easiest method** - just set an environment variable:

```bash
# Switch to LM Studio
export LLM_PROVIDER=lmstudio
export LMSTUDIO_BASE_URL=http://localhost:1234/v1

# Run your services
make services-start
```

### Option 2: Switch to LM Studio (Configuration File)

Edit `config/llm_providers.yaml`:

```yaml
# Change this line:
active_provider: ollama

# To this:
active_provider: lmstudio
```

Then restart services:

```bash
make services-restart
```

### Option 3: Switch Programmatically

```python
from src.services.llm_providers import LLMProviderFactory

# Create LM Studio provider
provider = LLMProviderFactory.create('lmstudio', {
    'base_url': 'http://localhost:1234/v1',
    'model': 'local-model',
    'timeout': 120
})

# Use it
async with provider:
    response = await provider.generate(LLMRequest(
        prompt="Analyze this market data...",
        model="local-model"
    ))
    print(response.text)
```

---

## 📋 Step-by-Step Migration

### Phase 1: Setup LM Studio

1. **Download and Install LM Studio**
   ```bash
   # macOS: Download from https://lmstudio.ai/
   # Or install via Homebrew:
   brew install --cask lm-studio
   ```

2. **Load a Model**
   - Open LM Studio
   - Go to "Discover" tab
   - Search for models (e.g., "Llama 2", "Mistral", "Gemma")
   - Download and load your preferred model
   - Click "Start Server" in the "Local Server" tab

3. **Verify Server**
   ```bash
   # Check if LM Studio is running
   curl http://localhost:1234/v1/models
   
   # Should return list of loaded models
   ```

### Phase 2: Update Configuration

1. **Edit Environment Variables**

   Create or edit `.env` file in project root:

   ```bash
   # LLM Provider Selection
   LLM_PROVIDER=lmstudio
   
   # LM Studio Configuration
   LMSTUDIO_BASE_URL=http://localhost:1234/v1
   LMSTUDIO_MODEL=local-model
   LMSTUDIO_TIMEOUT=120
   LMSTUDIO_MAX_RETRIES=3
   
   # Keep Ollama as fallback (optional)
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=gemma3:1b
   ```

2. **Or Edit Configuration File**

   Edit `config/llm_providers.yaml`:

   ```yaml
   # Change active provider
   active_provider: lmstudio
   
   # Configure LM Studio
   lmstudio:
     base_url: "http://localhost:1234/v1"
     model: "local-model"
     timeout: 120
     max_retries: 3
   
   # Configure fallback chain
   selection_strategy:
     mode: "fallback"
     fallback_chain:
       - lmstudio
       - ollama
   ```

### Phase 3: Update Services

**For most services, no code changes needed!** Just restart with new configuration.

```bash
# Restart trading services
make services-restart

# Or use wizard
make wizard
→ Service Management → services-restart
```

### Phase 4: Verify

1. **Check Provider Status**

   ```bash
   python3 -c "
   from src.services.llm_providers import LLMProviderFactory
   import asyncio
   
   async def check():
       provider = LLMProviderFactory.create_from_env()
       is_healthy = await provider.health_check()
       print(f'Provider: {provider.provider_type}')
       print(f'Healthy: {is_healthy}')
       models = await provider.list_models()
       print(f'Available models: {models}')
   
   asyncio.run(check())
   "
   ```

2. **Test Generation**

   ```bash
   python3 -c "
   from src.services.llm_providers import LLMProviderFactory, LLMRequest
   import asyncio
   
   async def test():
       provider = LLMProviderFactory.create_from_env()
       async with provider:
           response = await provider.generate(LLMRequest(
               prompt='What is 2+2?',
               model='local-model',
               temperature=0.3
           ))
           print(f'Response: {response.text}')
           print(f'Tokens: {response.tokens_used}')
           print(f'Latency: {response.latency_ms}ms')
   
   asyncio.run(test())
   "
   ```

---

## 🔧 Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | Active provider: `ollama`, `lmstudio`, `openai` |
| `LMSTUDIO_BASE_URL` | `http://localhost:1234/v1` | LM Studio server URL |
| `LMSTUDIO_MODEL` | `local-model` | Model name (LM Studio uses loaded model) |
| `LMSTUDIO_TIMEOUT` | `120` | Request timeout in seconds |
| `LMSTUDIO_MAX_RETRIES` | `3` | Maximum retry attempts |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `gemma3:1b` | Ollama model name |
| `OPENAI_API_KEY` | - | OpenAI API key (required for OpenAI) |
| `OPENAI_MODEL` | `gpt-3.5-turbo` | OpenAI model name |

### Configuration File Structure

```yaml
# config/llm_providers.yaml

# Which provider to use
active_provider: lmstudio  # ollama, lmstudio, openai

# Provider-specific settings
lmstudio:
  base_url: "http://localhost:1234/v1"
  model: "local-model"
  timeout: 120
  max_retries: 3

# Fallback strategy
selection_strategy:
  mode: "fallback"  # fallback, round_robin, cost_optimized
  fallback_chain:
    - lmstudio
    - ollama
```

---

## 💡 Use Cases

### Use Case 1: Development (LM Studio)

**Scenario**: You want easier model management with a GUI

**Configuration**:
```yaml
active_provider: lmstudio
lmstudio:
  base_url: "http://localhost:1234/v1"
```

**Benefits**:
- GUI for model management
- Easy model switching
- Resource monitoring
- No command-line needed

---

### Use Case 2: Production (Ollama)

**Scenario**: Headless server deployment

**Configuration**:
```yaml
active_provider: ollama
ollama:
  base_url: "http://ollama-server:11434"
  model: "gemma3:1b"
```

**Benefits**:
- Lightweight, no GUI
- Better for containers
- Command-line management
- Production-ready

---

### Use Case 3: Cloud Backup (OpenAI)

**Scenario**: Fallback to OpenAI if local fails

**Configuration**:
```yaml
active_provider: ollama
selection_strategy:
  mode: "fallback"
  fallback_chain:
    - ollama
    - lmstudio
    - openai
    
openai:
  api_key: "${OPENAI_API_KEY}"
  model: "gpt-3.5-turbo"
```

**Benefits**:
- Always available
- High quality responses
- Automatic fallback

---

### Use Case 4: Hybrid Setup

**Scenario**: Use LM Studio locally, Ollama in Kubernetes

**Configuration**:
```bash
# Local development
export LLM_PROVIDER=lmstudio
export LMSTUDIO_BASE_URL=http://localhost:1234/v1

# Kubernetes (in deployment YAML)
env:
  - name: LLM_PROVIDER
    value: "ollama"
  - name: OLLAMA_BASE_URL
    value: "http://ollama-controller.ollama-controller.svc.cluster.local:12001"
```

---

## 🧙 Wizard Integration

The wizard now supports provider switching!

```bash
make wizard
→ AI Assistant
  → llm-provider-status   # Check current provider
  → llm-switch-provider   # Switch providers
  → llm-test-provider     # Test current provider
```

### Provider Management Commands

```bash
# Check current provider
make llm-provider-status

# Switch to LM Studio
make llm-switch-lmstudio

# Switch to Ollama
make llm-switch-ollama

# Test provider
make llm-test-provider
```

---

## 🔍 Comparison: Ollama vs LM Studio

| Feature | Ollama | LM Studio |
|---------|--------|-----------|
| **Interface** | Command-line | GUI + CLI |
| **Model Management** | CLI commands | Visual interface |
| **API** | Native Ollama | OpenAI-compatible |
| **Resource Monitoring** | Terminal only | Built-in GUI |
| **Ease of Use** | Technical users | All users |
| **Container Friendly** | ✅ Excellent | ⚠️ GUI needed |
| **Model Loading** | Manual pull | Click to download |
| **API Compatibility** | Ollama format | OpenAI format |
| **Multi-Model** | Switch via API | Switch in GUI |
| **Headless** | ✅ Yes | ❌ No (needs GUI) |

### When to Use What

**Use Ollama when**:
- Deploying to Kubernetes/containers
- Running headless servers
- Prefer command-line tools
- Need lightweight deployment

**Use LM Studio when**:
- Local development on your Mac
- Want GUI for model management
- Prefer visual interfaces
- Need easy model switching

**Use Both when**:
- Development on Mac (LM Studio)
- Production on Kubernetes (Ollama)
- Want flexibility

---

## 🐛 Troubleshooting

### Problem: Provider not found

**Error**: `ValueError: Unsupported provider type: lmstudio`

**Solution**:
```python
# Check if provider is registered
from src.services.llm_providers import LLMProviderFactory
print(LLMProviderFactory.get_supported_providers())
# Should show: ['ollama', 'lmstudio', 'openai']
```

---

### Problem: LM Studio not responding

**Error**: `LM Studio health check failed`

**Solutions**:
1. **Start LM Studio server**
   - Open LM Studio
   - Go to "Local Server" tab
   - Click "Start Server"

2. **Check port**
   ```bash
   curl http://localhost:1234/v1/models
   ```

3. **Verify URL in config**
   ```bash
   echo $LMSTUDIO_BASE_URL
   # Should be: http://localhost:1234/v1
   ```

---

### Problem: Model not loaded

**Error**: `Model not available`

**Solutions**:
1. **Load model in LM Studio**
   - Open LM Studio
   - Select a model from list
   - Click "Load Model"

2. **Use generic model name**
   ```python
   # LM Studio uses the currently loaded model
   model="local-model"  # This works regardless of which model is loaded
   ```

---

### Problem: Switching providers doesn't work

**Symptom**: Still using old provider after changing config

**Solutions**:
1. **Restart services**
   ```bash
   make services-restart
   ```

2. **Check environment variables override config**
   ```bash
   env | grep LLM_PROVIDER
   # If set, it overrides config file
   ```

3. **Clear and reload**
   ```bash
   unset LLM_PROVIDER
   export LLM_PROVIDER=lmstudio
   make services-restart
   ```

---

## 📊 Performance Comparison

Based on typical usage with Gemma 3:1B on MacBook Pro M3:

| Metric | Ollama | LM Studio |
|--------|--------|-----------|
| **Startup Time** | ~2s | ~5s (GUI) |
| **First Request** | ~3s | ~3s |
| **Subsequent Requests** | ~1s | ~1s |
| **Memory Usage** | ~2GB | ~2.5GB (+ GUI) |
| **CPU Usage** | Similar | Similar |
| **Ease of Setup** | Medium | Easy |

**Conclusion**: Performance is comparable. Choice depends on use case and preference.

---

## 🎓 Advanced Topics

### Custom Provider

Create your own provider:

```python
from src.services.llm_providers.base import LLMProvider, LLMProviderType

class CustomProvider(LLMProvider):
    def _get_provider_type(self) -> LLMProviderType:
        return LLMProviderType.CUSTOM
    
    async def initialize(self) -> bool:
        # Your initialization logic
        pass
    
    # Implement other abstract methods...

# Register it
LLMProviderFactory.register_provider(
    LLMProviderType.CUSTOM,
    CustomProvider
)
```

### Dynamic Provider Switching

Switch providers at runtime:

```python
from src.services.llm_providers import LLMProviderFactory

# Start with Ollama
provider = LLMProviderFactory.create('ollama')

try:
    response = await provider.generate(request)
except LLMError:
    # Fallback to LM Studio
    await provider.cleanup()
    provider = LLMProviderFactory.create('lmstudio')
    response = await provider.generate(request)
```

---

## 📚 Related Documentation

- **Provider Base Interface**: `src/services/llm_providers/base.py`
- **Factory Pattern**: `src/services/llm_providers/factory.py`
- **Configuration**: `config/llm_providers.yaml`
- **Wizard Integration**: `scripts/wizard.py`

---

## ✅ Migration Checklist

- [ ] Install LM Studio (if using)
- [ ] Load a model in LM Studio
- [ ] Start LM Studio server
- [ ] Update environment variables or config file
- [ ] Test provider health check
- [ ] Test generation
- [ ] Restart services
- [ ] Verify trading system works
- [ ] Update deployment configs (K8s)
- [ ] Document your choice

---

## 🎉 Summary

Your system now supports:

✅ **Multiple LLM providers** (Ollama, LM Studio, OpenAI)  
✅ **Easy configuration** (env vars or YAML)  
✅ **Automatic fallback** (if primary fails)  
✅ **Unified API** (same code works with any provider)  
✅ **Wizard integration** (switch providers from wizard)  

**Switch providers anytime** with just a configuration change - no code changes needed!

---

**Quick Commands**:

```bash
# Switch to LM Studio
export LLM_PROVIDER=lmstudio
make services-restart

# Switch to Ollama
export LLM_PROVIDER=ollama
make services-restart

# Test current provider
python3 -c "from src.services.llm_providers import LLMProviderFactory; import asyncio; asyncio.run(LLMProviderFactory.create_from_env().health_check())"
```

🎊 **Your system is now provider-agnostic!** 🎊








