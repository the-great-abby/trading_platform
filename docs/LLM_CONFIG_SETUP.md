# 🔧 LLM Provider Configuration Setup

**Quick Guide**: Set your LLM provider once, never pass variables again!

---

## 🎯 The Three Ways to Configure

### Option 1: Configuration File (Recommended) ⭐

**Best for**: Permanent settings that you commit to git

**File**: `config/llm_providers.yaml`

**Edit this**:

```yaml
# Line 5 - Change your default provider
active_provider: lmstudio  # Change from 'ollama' to 'lmstudio'

# Then customize the provider settings
lmstudio:
  base_url: "http://localhost:1234/v1"
  model: "local-model"
  timeout: 120
  max_retries: 3
```

**That's it!** Now every service uses LM Studio by default.

---

### Option 2: Environment File (Flexible) 🔄

**Best for**: Local development, per-developer settings

**File**: Create `.env` in project root

**Steps**:

1. **Create the file**:
   ```bash
   cd /Users/abby/code/trading
   cat > .env << 'EOF'
   # LLM Provider Configuration
   LLM_PROVIDER=lmstudio
   LMSTUDIO_BASE_URL=http://localhost:1234/v1
   LMSTUDIO_MODEL=local-model
   EOF
   ```

2. **Load it automatically** (add to your shell profile):
   ```bash
   # Add to ~/.zshrc or ~/.bashrc
   if [ -f ~/code/trading/.env ]; then
       set -a
       source ~/code/trading/.env
       set +a
   fi
   ```

3. **Or load manually** when needed:
   ```bash
   source scripts/load_llm_config.sh
   ```

**Benefits**:
- ✅ Persists across terminal sessions
- ✅ Not committed to git (`.env` is in `.gitignore`)
- ✅ Easy to change per developer

---

### Option 3: Shell Profile (Always Active) 🌍

**Best for**: System-wide default that applies everywhere

**File**: `~/.zshrc` (or `~/.bashrc` for bash)

**Add these lines**:

```bash
# LLM Provider Configuration
export LLM_PROVIDER=lmstudio
export LMSTUDIO_BASE_URL=http://localhost:1234/v1
export LMSTUDIO_MODEL=local-model
```

**Reload**:
```bash
source ~/.zshrc
```

**Benefits**:
- ✅ Works in every terminal
- ✅ Persists across reboots
- ✅ No need to load anything

---

## 📋 Quick Setup Guide

### For LM Studio as Default

**Method 1: Config File** (Recommended)

```bash
# Edit the config file
nano config/llm_providers.yaml

# Change line 5 to:
active_provider: lmstudio
```

**Method 2: Create .env file**

```bash
# Create .env file
cat > .env << 'EOF'
LLM_PROVIDER=lmstudio
LMSTUDIO_BASE_URL=http://localhost:1234/v1
EOF

# Add to your shell profile
echo 'source ~/code/trading/scripts/load_llm_config.sh' >> ~/.zshrc
source ~/.zshrc
```

**Method 3: Shell Profile**

```bash
# Add to ~/.zshrc
cat >> ~/.zshrc << 'EOF'

# LLM Provider Configuration
export LLM_PROVIDER=lmstudio
export LMSTUDIO_BASE_URL=http://localhost:1234/v1
EOF

# Reload
source ~/.zshrc
```

---

## 🔍 Configuration Priority

The system checks for configuration in this order:

```
1. Environment Variables (highest priority)
   ↓
2. .env file (if exists)
   ↓
3. config/llm_providers.yaml (default)
   ↓
4. Built-in defaults (lowest priority)
```

So if you set `LLM_PROVIDER=ollama` as an environment variable, it will override the config file.

---

## ✅ Verify Your Configuration

### Check Current Provider

```bash
# Quick check
echo $LLM_PROVIDER

# Detailed check
python3 -c "
import os
from src.services.llm_providers import LLMProviderFactory

provider_type = os.getenv('LLM_PROVIDER', 'from config file')
print(f'Provider: {provider_type}')

provider = LLMProviderFactory.create_from_env()
print(f'Type: {provider.provider_type}')
print(f'Config: {provider.config}')
"
```

### Test It Works

```bash
# Test the provider
python3 examples/llm_provider_example.py

# Should show:
# Provider: lmstudio
# Health: ✅ Healthy
```

---

## 🎨 Example Configurations

### Example 1: LM Studio for Development

**File**: `config/llm_providers.yaml`

```yaml
active_provider: lmstudio

lmstudio:
  base_url: "http://localhost:1234/v1"
  model: "local-model"
  timeout: 120

# Fallback to Ollama if LM Studio is down
selection_strategy:
  mode: "fallback"
  fallback_chain:
    - lmstudio
    - ollama
```

---

### Example 2: Ollama for Production

**File**: `config/llm_providers.yaml`

```yaml
active_provider: ollama

ollama:
  base_url: "http://ollama-controller.ollama-controller.svc.cluster.local:12001"
  model: "gemma3:1b"
  timeout: 120
```

---

### Example 3: Hybrid Setup

**Local Development**: `.env` file

```bash
LLM_PROVIDER=lmstudio
LMSTUDIO_BASE_URL=http://localhost:1234/v1
```

**Kubernetes Production**: In deployment YAML

```yaml
env:
  - name: LLM_PROVIDER
    value: "ollama"
  - name: OLLAMA_BASE_URL
    value: "http://ollama-controller:12001"
```

---

## 🔄 Switching Providers

### Permanent Switch (Config File)

```bash
# Edit config
nano config/llm_providers.yaml

# Change: active_provider: lmstudio
# Restart services
make services-restart
```

### Temporary Switch (Environment Variable)

```bash
# This session only
export LLM_PROVIDER=lmstudio
make services-restart

# Next session will use config file default
```

### Per-Service Override (Advanced)

```bash
# Service 1 uses LM Studio
LLM_PROVIDER=lmstudio python3 run/service1.py &

# Service 2 uses Ollama
LLM_PROVIDER=ollama python3 run/service2.py &
```

---

## 📍 File Locations Summary

| File | Purpose | Committed to Git? |
|------|---------|-------------------|
| `config/llm_providers.yaml` | Default config | ✅ Yes |
| `.env` | Local overrides | ❌ No (in .gitignore) |
| `~/.zshrc` | Shell profile | ❌ Personal file |
| Kubernetes YAML | Production config | ✅ Yes |

---

## 🎯 Recommended Setup

**For Your Use Case** (local development + Kubernetes production):

1. **Set default in config file**:
   ```yaml
   # config/llm_providers.yaml
   active_provider: lmstudio  # Your local default
   ```

2. **Override in Kubernetes**:
   ```yaml
   # k8s/deployments/*.yaml
   env:
     - name: LLM_PROVIDER
       value: "ollama"  # Production uses Ollama
   ```

3. **No environment variables needed locally!**

---

## 🐛 Troubleshooting

### Problem: Provider not changing

**Check**:
```bash
# Are environment variables set?
env | grep LLM_PROVIDER

# If yes, they override config file
unset LLM_PROVIDER
```

### Problem: Can't find config file

**Fix**:
```bash
# Verify file exists
ls -la config/llm_providers.yaml

# If missing, it was created in this session:
# Just restart your services and it will be picked up
```

### Problem: Configuration not loading

**Debug**:
```python
# Check what's being loaded
from src.services.llm_providers.factory import LLMProviderFactory
import os

print(f"LLM_PROVIDER env: {os.getenv('LLM_PROVIDER', 'not set')}")
config = LLMProviderFactory._load_config_from_env('lmstudio')
print(f"Config: {config}")
```

---

## 📝 Quick Commands

```bash
# Method 1: Edit config file (permanent)
nano config/llm_providers.yaml

# Method 2: Create .env file (flexible)
echo "LLM_PROVIDER=lmstudio" > .env

# Method 3: Add to shell profile (always active)
echo "export LLM_PROVIDER=lmstudio" >> ~/.zshrc && source ~/.zshrc

# Test configuration
python3 examples/llm_provider_example.py

# Check what's active
echo $LLM_PROVIDER
```

---

## 🎉 Summary

**Your Question**: "Where do we adjust the config so we don't need to pass in a variable?"

**Answer**: Three options, pick one:

1. **Config file**: `config/llm_providers.yaml` (line 5)
   - ✅ Best for: Team defaults
   - ✅ Committed to git
   - ✅ No variables needed

2. **`.env` file**: Create in project root
   - ✅ Best for: Personal settings
   - ✅ Not in git
   - ✅ Per-developer customization

3. **Shell profile**: `~/.zshrc`
   - ✅ Best for: System-wide default
   - ✅ Always active
   - ✅ Works everywhere

**Recommended**: Edit `config/llm_providers.yaml` and change line 5 to `active_provider: lmstudio`

**That's it!** No more passing variables! 🎊








