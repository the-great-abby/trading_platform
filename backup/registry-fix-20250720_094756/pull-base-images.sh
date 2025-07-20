#!/bin/bash

# Script to pull and store base images in local registry
# This speeds up Docker builds by avoiding repeated downloads from Docker Hub

set -e

REGISTRY="localhost:5000"

echo "Pulling and storing base images in local registry..."

# Python images
echo "Processing Python images..."
docker pull python:3.11-slim
docker tag python:3.11-slim $REGISTRY/python:3.11-slim
docker push $REGISTRY/python:3.11-slim

# Database images
echo "Processing database images..."
docker pull postgres:15-alpine
docker tag postgres:15-alpine $REGISTRY/postgres:15-alpine
docker push $REGISTRY/postgres:15-alpine

# Cache/Message broker images
echo "Processing cache and message broker images..."
docker pull redis:7-alpine
docker tag redis:7-alpine $REGISTRY/redis:7-alpine
docker push $REGISTRY/redis:7-alpine

docker pull rabbitmq:3-management-alpine
docker tag rabbitmq:3-management-alpine $REGISTRY/rabbitmq:3-management-alpine
docker push $REGISTRY/rabbitmq:3-management-alpine

# Additional useful images
echo "Processing additional utility images..."
docker pull nginx:alpine
docker tag nginx:alpine $REGISTRY/nginx:alpine
docker push $REGISTRY/nginx:alpine

docker pull busybox:latest
docker tag busybox:latest $REGISTRY/busybox:latest
docker push $REGISTRY/busybox:latest

echo "All base images have been pulled and stored in local registry!"
echo "Available images in local registry:"
docker images | grep localhost:5000 