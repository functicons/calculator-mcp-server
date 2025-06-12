#!/bin/bash
set -e
IMAGE_NAME="shell-mcp-server"
IMAGE_TAG="latest"
echo "Building Docker image ${IMAGE_NAME}:${IMAGE_TAG}..."
# Build from the current directory (project root)
docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .
echo "Docker image ${IMAGE_NAME}:${IMAGE_TAG} built successfully."
