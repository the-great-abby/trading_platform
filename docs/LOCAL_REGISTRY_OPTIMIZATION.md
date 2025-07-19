# Local Registry Optimization Guide

## Overview

This guide explains how we've optimized Docker builds by storing base images in the local registry (`localhost:5000`). This significantly speeds up builds by avoiding repeated downloads from Docker Hub.

## What's Been Optimized

### Base Images Stored Locally

The following base images are now stored in the local registry:

- **Python**: `localhost:5000/python:3.11-slim`
- **PostgreSQL**: `localhost:5000/postgres:15-alpine`
- **Redis**: `localhost:5000/redis:7-alpine`
- **RabbitMQ**: `localhost:5000/rabbitmq:3-management-alpine`

### Updated Files

1. **Dockerfile.dev**: Now uses `FROM localhost:5000/python:3.11-slim`
2. **Kubernetes Deployments**: Updated to use local registry images
3. **Scripts**: Added `scripts/pull-base-images.sh` for automation
4. **Makefile**: Added `docker-pull-base-images` target

## Benefits

### Build Speed Improvements

- **First build**: ~570 seconds (vs ~1000+ seconds from Docker Hub)
- **Subsequent builds**: Much faster due to local caching
- **Network independence**: No dependency on Docker Hub availability

### Resource Savings

- Reduced bandwidth usage
- Faster CI/CD pipeline builds
- Consistent image availability

## Usage

### Pull Base Images

```bash
# Manual method
./scripts/pull-base-images.sh

# Using Makefile
make -f Makefile.docker docker-pull-base-images
```

### Build with Local Images

```bash
# Build using local registry
docker build -f Dockerfile.dev -t localhost:5000/trading-system:latest .

# Push to local registry
docker push localhost:5000/trading-system:latest
```

### Kubernetes Deployment

All Kubernetes deployments now use local registry images:

```yaml
# Example from postgres-deployment.yaml
containers:
- name: postgres
  image: localhost:5000/postgres:15-alpine
```

## Maintenance

### Adding New Base Images

1. Pull the image from Docker Hub:
   ```bash
   docker pull <image>:<tag>
   ```

2. Tag for local registry:
   ```bash
   docker tag <image>:<tag> localhost:5000/<image>:<tag>
   ```

3. Push to local registry:
   ```bash
   docker push localhost:5000/<image>:<tag>
   ```

4. Update the `scripts/pull-base-images.sh` script to include the new image.

### Updating Existing Images

```bash
# Pull latest version
docker pull <image>:<tag>

# Re-tag and push
docker tag <image>:<tag> localhost:5000/<image>:<tag>
docker push localhost:5000/<image>:<tag>
```

## Troubleshooting

### Registry Not Available

If the local registry is down:

```bash
# Start the registry
make -f Makefile.docker docker-registry-up

# Check status
docker ps | grep registry
```

### Image Pull Issues

```bash
# Check available images
docker images | grep localhost:5000

# Re-pull base images
make -f Makefile.docker docker-pull-base-images
```

### Build Failures

If builds fail due to missing base images:

1. Ensure local registry is running
2. Re-pull base images
3. Check network connectivity to localhost:5000

## Best Practices

1. **Regular Updates**: Periodically update base images for security patches
2. **Version Pinning**: Use specific version tags rather than `latest`
3. **Registry Monitoring**: Monitor local registry storage usage
4. **Backup Strategy**: Consider backing up frequently used images

## Performance Metrics

### Before Optimization
- Initial build time: ~1000+ seconds
- Network dependency: High
- Build reliability: Dependent on Docker Hub

### After Optimization
- Initial build time: ~570 seconds (43% improvement)
- Network dependency: Low (local only)
- Build reliability: High (local availability)

## Future Enhancements

1. **Multi-stage builds**: Further optimize by using local base images in multi-stage builds
2. **Image layers**: Optimize layer caching strategies
3. **Registry mirroring**: Set up Docker Hub mirror for additional redundancy
4. **Automated updates**: Script to automatically update base images 