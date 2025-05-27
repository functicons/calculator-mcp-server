#!/bin/bash
set -ex
IMAGE_NAME="calculator-mcp-server"
IMAGE_TAG="latest"
CONTAINER_NAME="mcp-calculator-inspector" # Different name for inspector container
HOST_MCP_PORT="6277" 
HOST_INSPECTOR_PORT="6274"
CONTAINER_MCP_PORT="6277" # Port for mcp dev server inside container
CONTAINER_INSPECTOR_PORT="6274" # Port for inspector inside container

# Ensure the image is built
if ! docker image inspect "${IMAGE_NAME}:${IMAGE_TAG}" &> /dev/null; then
    echo "Docker image ${IMAGE_NAME}:${IMAGE_TAG} not found. Building it first..."
    if [ -f ./build-image.sh ]; then
        ./build-image.sh
    else
        echo "Error: build-image.sh not found. Please build the image manually."
        exit 1
    fi
fi

echo "Attempting to start Docker container ${CONTAINER_NAME} with MCP Inspector..."

if [ "$(docker ps -q -f name=${CONTAINER_NAME})" ]; then
    echo "Container ${CONTAINER_NAME} is already running. Stopping and removing it first..."
    docker stop "${CONTAINER_NAME}" && docker rm "${CONTAINER_NAME}"
elif [ "$(docker ps -aq -f status=exited -f name=${CONTAINER_NAME})" ]; then
    echo "Container ${CONTAINER_NAME} exists but is stopped. Removing it..."
    docker rm "${CONTAINER_NAME}"
fi

echo "Starting new container ${CONTAINER_NAME}..."
# Note: mcp dev uses stdio by default, the --host and --port here are for the server it manages.
# The inspector itself runs on --inspector-port.
# We map both ports.
docker run -d \
    -p "${HOST_MCP_PORT}:${CONTAINER_MCP_PORT}" \
    -p "${HOST_INSPECTOR_PORT}:${CONTAINER_INSPECTOR_PORT}" \
    --name "${CONTAINER_NAME}" \
    "${IMAGE_NAME}:${IMAGE_TAG}" \
    mcp dev src/calculator_server.py

echo "Container ${CONTAINER_NAME} started."
echo "MCP Server (proxied by mcp dev) should be accessible at http://localhost:${HOST_MCP_PORT}/mcp"
echo "MCP Inspector UI should be accessible at http://localhost:${HOST_INSPECTOR_PORT}"
echo "To see logs: docker logs ${CONTAINER_NAME}"
echo "To stop this server & inspector: docker stop ${CONTAINER_NAME} && docker rm ${CONTAINER_NAME}"
