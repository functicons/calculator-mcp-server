#!/bin/bash
set -e

IMAGE_NAME="calculator-mcp-server"
IMAGE_TAG="latest"

echo "Ensuring Docker image ${IMAGE_NAME}:${IMAGE_TAG} is up to date..."
# Call build-image.sh to build or rebuild the image
# Assuming build-image.sh is in the same directory
if [ -f ./build-image.sh ]; then
    ./build-image.sh
else
    echo "Error: build-image.sh not found. Cannot ensure image is up to date."
    # Optionally, exit if build script is crucial and not found
    # exit 1 
    # Or, proceed with a warning if the image might already exist
    echo "Warning: Proceeding with existing image if available."
fi


echo "Running unit tests in Docker container from image ${IMAGE_NAME}:${IMAGE_TAG}..."

# Ensure the image exists after attempting to build
if ! docker image inspect "${IMAGE_NAME}:${IMAGE_TAG}" &> /dev/null; then
    echo "Docker image ${IMAGE_NAME}:${IMAGE_TAG} not found even after build attempt."
    echo "Please check build-image.sh and Dockerfile for errors."
    exit 1
fi

# Run pytest inside the Docker container using 'python3 -m pytest'
# --rm automatically removes the container when it exits.
# The working directory inside the container is /app (set in Dockerfile).
# pytest will look for tests in the 'tests' directory relative to /app.
docker run --rm "${IMAGE_NAME}:${IMAGE_TAG}" python3 -m pytest tests/ -vv

echo "Tests finished."
