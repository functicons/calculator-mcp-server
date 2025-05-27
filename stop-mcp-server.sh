#!/bin/bash
set -e

CONTAINER_NAME="calculator-mcp-server"

echo "Attempting to stop and remove Docker container ${CONTAINER_NAME}..."
if docker ps -q -f name=${CONTAINER_NAME} | grep -q .; then # Check if container is running
    echo "Stopping container ${CONTAINER_NAME}..."
    docker stop "${CONTAINER_NAME}"
else
    echo "Container ${CONTAINER_NAME} is not running."
fi
if docker ps -aq -f name=${CONTAINER_NAME} | grep -q .; then # Check if container exists (even if stopped)
    echo "Removing container ${CONTAINER_NAME}..."
    docker rm "${CONTAINER_NAME}"
else
    echo "Container ${CONTAINER_NAME} does not exist."
fi
echo "Container ${CONTAINER_NAME} processed."
