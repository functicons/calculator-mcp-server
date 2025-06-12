#!/bin/bash
set -ex

# Usage: ./start-mcp-server-with-inspector.sh [-v /path/on/host:/path/in/container] ...
# Additional arguments are passed to docker run, for example, to mount volumes.

declare -a VOLUME_ARGS=()
# Parse command-line arguments for volume mounts
PASSTHROUGH_ARGS=() # To collect non-script arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -v|--volume)
            if [ -z "$2" ]; then
                echo "Error: Argument for $1 is missing" >&2
                exit 1
            fi
            VOLUME_ARGS+=("-v" "$2")
            shift # past argument
            shift # past value
            ;;
        *) # unknown option or an argument for mcp dev
            PASSTHROUGH_ARGS+=("$1")
            shift # past argument
            ;;
    esac
done


IMAGE_NAME="shell-mcp-server"
IMAGE_TAG="latest"
CONTAINER_NAME="mcp-shell-inspector" # Different name for inspector container
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
    "${VOLUME_ARGS[@]}" \
    "${IMAGE_NAME}:${IMAGE_TAG}" \
    mcp dev src/shell_server.py "${PASSTHROUGH_ARGS[@]}" # Pass any remaining args to mcp dev

echo "Container ${CONTAINER_NAME} started."
echo "MCP Server (proxied by mcp dev) should be accessible at http://localhost:${HOST_MCP_PORT}/mcp"
echo "MCP Inspector UI should be accessible at http://localhost:${HOST_INSPECTOR_PORT}"
echo "To see logs: docker logs ${CONTAINER_NAME}"
echo "To stop this server & inspector: docker stop ${CONTAINER_NAME} && docker rm ${CONTAINER_NAME}"
