# 🐳 Local Docker Registry Setup

Your local Docker registry is configured at `host.docker.internal:5000`. Here's what's been set up for you:

## 📁 New Files Created

- `scripts/docker-registry-setup.sh` - Main registry management script
- `scripts/setup-local-registry.sh` - Registry setup and configuration script
- `Makefile.registry` - Registry-specific Makefile operations
- `docker-compose.registry.yml` - Docker Compose override for registry images
- `docs/LOCAL_REGISTRY_GUIDE.md` - Comprehensive registry guide

## 🚀 Quick Start

### 1. Set up the registry (if not already running)
```bash
./scripts/setup-local-registry.sh setup
```

### 2. Complete registry setup
```bash
make registry-setup
```

### 3. Deploy with registry images
```bash
make k8s-deploy-registry
```

## 🛠️ Available Commands

### Main Makefile (delegates to Makefile.registry)
```bash
make registry-check          # Check registry accessibility
make registry-setup          # Complete setup (build, push, config, update-k8s)
make registry-build          # Build all images for registry
make registry-push           # Push all images to registry
make registry-build-push     # Build and push all images
make k8s-deploy-registry     # Deploy to Kubernetes with registry images
```

### Direct Script Usage
```bash
./scripts/docker-registry-setup.sh check      # Check registry
./scripts/docker-registry-setup.sh build      # Build images
./scripts/docker-registry-setup.sh push       # Push images
./scripts/docker-registry-setup.sh all        # Complete setup
```

### Registry Management
```bash
./scripts/setup-local-registry.sh setup       # Set up registry
./scripts/setup-local-registry.sh check       # Check status
./scripts/setup-local-registry.sh restart     # Restart registry
```

## 🔧 Configuration

### Registry Host
- **Host**: `host.docker.internal:5000`
- **Project**: `trading-bot`
- **Default Tag**: `latest`

### Image Naming Convention
- Main image: `host.docker.internal:5000/trading-bot:latest`
- Service images: `host.docker.internal:5000/trading-bot-{service}:latest`

### Docker Compose with Registry
```bash
# Use registry images
docker-compose -f docker-compose.yml -f docker-compose.registry.yml up -d

# Build and use registry images
docker-compose -f docker-compose.yml -f docker-compose.registry.yml up -d --build
```

## 📊 Registry Information

### API Endpoints
- **Catalog**: http://host.docker.internal:5000/v2/_catalog
- **Health**: http://host.docker.internal:5000/v2/

### Useful Commands
```bash
# List all images in registry
curl http://host.docker.internal:5000/v2/_catalog

# List tags for trading-bot
curl http://host.docker.internal:5000/v2/trading-bot/tags/list

# Check registry health
curl http://host.docker.internal:5000/v2/
```

## 🔄 Development Workflow

1. **Make code changes**
2. **Build and push to registry**
   ```bash
   make registry-build-push
   ```
3. **Deploy with new images**
   ```bash
   make k8s-deploy-registry
   ```
4. **Test and iterate**

## 🐛 Troubleshooting

### Registry Not Accessible
```bash
# Check if registry is running
./scripts/setup-local-registry.sh check

# Set up registry if needed
./scripts/setup-local-registry.sh setup
```

### Docker Daemon Configuration
For macOS (Docker Desktop):
1. Open Docker Desktop
2. Go to Settings/Preferences → Docker Engine
3. Add to JSON configuration:
   ```json
   {
     "insecure-registries": ["host.docker.internal:5000"]
   }
   ```
4. Click 'Apply & Restart'

### Image Push Failures
```bash
# Check registry accessibility
make registry-check

# Rebuild and push
make registry-build-push
```

## 📚 Documentation

- **Full Guide**: `docs/LOCAL_REGISTRY_GUIDE.md`
- **Registry Script**: `scripts/docker-registry-setup.sh --help`
- **Setup Script**: `scripts/setup-local-registry.sh --help`

## 🎯 Next Steps

1. **Set up the registry**: `./scripts/setup-local-registry.sh setup`
2. **Configure Docker daemon** (if needed)
3. **Build and push images**: `make registry-setup`
4. **Deploy to Kubernetes**: `make k8s-deploy-registry`
5. **Test your deployment**

Your local registry is now ready to use! 🎉 