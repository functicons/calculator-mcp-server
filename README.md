
# Calculator MCP Server

The Calculator MCP Server is a backend service designed to provide arithmetic calculation capabilities to AI models, particularly Large Language Models (LLMs), via the Model Context Protocol (MCP). It allows LLMs to offload mathematical computations, ensuring accuracy and reliability for numerical queries.

This server is built on top of the official [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) and implements a single MCP tool named `calculator_tool` that accepts a string-based arithmetic expression and returns the calculated numerical result.

The server is packaged as a Docker image.

## Features

* **MCP Compliant:** Adheres to the Model Context Protocol for seamless integration.
* **Accurate Calculations:** Provides precise results for basic arithmetic operations (+, -, \*, /).
* **Safe Evaluation:** Uses a secure method to parse and evaluate mathematical expressions, preventing arbitrary code execution.
* **Standardized API:** Exposes functionality through the `tools/call` MCP method.
* **Dockerized:** Includes a Dockerfile for easy containerization, deployment, and testing.
* **Comprehensive Error Handling:** Returns structured JSON-RPC errors for invalid inputs or calculation issues.

## Prerequisites

* Docker
* `bash` (for running helper scripts)
* Python 3.12 (for understanding the code, not strictly for running if using Docker for everything)

## Setup and Installation

### 1. Clone the Repository (if applicable)

If this project is in a Git repository, clone it:
```bash
git clone <repository-url>
cd calculator-mcp-server
```

### 2. Build the Docker Image (Optional - Handled by `run-tests.sh` and `start-mcp-server.sh` if needed)

You can manually build the image:
```bash
./build-image.sh
```
However, `./run-tests.sh` will automatically build the image if it doesn't exist or if you want to ensure it's up-to-date before testing. Similarly, `start-mcp-server.sh` might incorporate this.

### 3. Running the Server

To start the server:
```bash
./start-mcp-server.sh
```
This script will ensure the image is built, start the server in a Docker container, and check its status. The server listens on port 8000 by default.

## Usage

The Calculator MCP Server exposes its functionality via MCP. An MCP client (e.g., an LLM host application) would interact with it as follows:

1.  **Initialize Connection:** The client establishes a connection with the server (running in Docker).
2.  **Tool Discovery (Optional but Recommended):** The client sends a `tools/list` request.
3.  **Tool Invocation:** The client sends a `tools/call` request to use the `calculator_tool`.

    **Request:**
    ```json
    {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "calculator_tool",
            "arguments": {
                "expression": "10 * (2 + 3) - 5 / 2"
            }
        },
        "id": "request-id-123"
    }
    ```

    **Successful Response:**
    ```json
    {
        "jsonrpc": "2.0",
        "result": {
            "value": 47.5
        },
        "id": "request-id-123"
    }
    ```

### Testing with `test-mcp-client.sh`

A simple CLI client script is provided to test the running server. Make sure the server is running via `./start-mcp-server.sh`.

```bash
./test-mcp-client.sh list"
```

```bash
./test-mcp-client.sh call "2+2"
```

## Running Tests

Unit tests are run inside a Docker container. The script handles building the image if necessary.
```bash
./run-tests.sh
```
This script first calls `./build-image.sh` to ensure the Docker image is up-to-date, then executes `pytest` within a new container instance.

## Stopping the Server (Docker)

If you started the server using `./start-mcp-server.sh`, you can stop it with:
```bash
./stop-mcp-server.sh
```

## Contributing

Please refer to the [developer_guide.md](./developer_guide.md).
