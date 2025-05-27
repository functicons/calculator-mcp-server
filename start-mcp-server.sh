#!/bin/bash

set -e

IMAGE_NAME="calculator-mcp-server"
IMAGE_TAG="latest"
CONTAINER_NAME="calculator-mcp-server"
HOST_PORT="8080" # Port on the host
SERVER_URL="http://localhost:${HOST_PORT}"

# Optional: Docker network settings
# To use a Docker network, set DOCKER_NETWORK_NAME.
# The DOCKER_NETWORK_HOSTNAME will be used as the container's hostname within that network.
#DOCKER_NETWORK_NAME="docker-network" # Example: "docker-network". Leave empty to not use a specific network.
#DOCKER_NETWORK_HOSTNAME="calculator-mcp-server" # Only used if DOCKER_NETWORK_NAME is set.

# --- Script Start ---

# Function to print error messages and exit
error_exit() {
    echo "Error: $1" >&2
    exit 1
}

# Ensure the image is built before trying to run it
if ! docker image inspect "${IMAGE_NAME}:${IMAGE_TAG}" &> /dev/null; then
    echo "Docker image ${IMAGE_NAME}:${IMAGE_TAG} not found. Building it first..."
    if [ -f ./build-image.sh ]; then
        ./build-image.sh
    else
        error_exit "build-image.sh not found. Please build the image ${IMAGE_NAME}:${IMAGE_TAG} manually."
    fi
fi

echo "Attempting to start Docker container ${CONTAINER_NAME} from image ${IMAGE_NAME}:${IMAGE_TAG}..."

# Check if container is running and stop/remove if necessary
if [ "$(docker ps -q -f name=^/${CONTAINER_NAME}$)" ]; then # Added ^/ and $ for exact name matching
    echo "Container ${CONTAINER_NAME} is already running. Stopping and removing it first..."
    docker stop "${CONTAINER_NAME}" > /dev/null && docker rm "${CONTAINER_NAME}" > /dev/null
elif [ "$(docker ps -aq -f status=exited -f name=^/${CONTAINER_NAME}$)" ]; then # Added ^/ and $ for exact name matching
    echo "Container ${CONTAINER_NAME} exists but is stopped. Removing it..."
    docker rm "${CONTAINER_NAME}" > /dev/null
fi

# Prepare docker run arguments
DOCKER_RUN_ARGS=(
    -d
    -p "127.0.0.1:${HOST_PORT}:8080"
    --name "${CONTAINER_NAME}"
)

# Check if DOCKER_NETWORK_NAME is specified
if [ -n "${DOCKER_NETWORK_NAME}" ]; then
    echo "Docker network '${DOCKER_NETWORK_NAME}' is specified."
    # Check if the specified Docker network exists
    if ! docker network inspect "${DOCKER_NETWORK_NAME}" &> /dev/null; then
        error_exit "Docker network '${DOCKER_NETWORK_NAME}' not found. Please create it first (e.g., using 'docker network create ${DOCKER_NETWORK_NAME}')."
    fi
    echo "Using Docker network '${DOCKER_NETWORK_NAME}' and hostname '${DOCKER_NETWORK_HOSTNAME}'."
    DOCKER_RUN_ARGS+=(--network "${DOCKER_NETWORK_NAME}")
    DOCKER_RUN_ARGS+=(--hostname "${DOCKER_NETWORK_HOSTNAME}")
else
    echo "No specific Docker network specified. Running container on the default bridge network."
fi

DOCKER_RUN_ARGS+=("${IMAGE_NAME}:${IMAGE_TAG}")

echo "Starting new container ${CONTAINER_NAME} with the following command:"
echo "docker run ${DOCKER_RUN_ARGS[*]}" # Print the command for clarity
set -x # Enable command echoing
docker run "${DOCKER_RUN_ARGS[@]}"
set +x # Disable command echoing

echo "Container ${CONTAINER_NAME} started."
echo "Server should be accessible on ${SERVER_URL}/mcp"
echo "To see logs: docker logs ${CONTAINER_NAME}"
echo "To list tools provided by the server: ./test-mcp-client.sh list" # Assuming this script exists
echo "To stop the server: ./stop-mcp-server.sh" # Assuming this script exists
