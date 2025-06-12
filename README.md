
# Shell MCP Server

The Shell MCP Server is a backend service designed to provide shell command execution capabilities to AI models, particularly Large Language Models (LLMs), via the Model Context Protocol (MCP). It allows LLMs to offload shell command execution, enabling them to interact with the system environment.
For example, when the user asks the LLM "what are the files in the current directory?", the LLM will call the server with "ls -la" to perform the command first and then answer the user.

This server is built on top of the official [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) and implements a single MCP tool named `shell_tool` that accepts a string-based shell command and returns its standard output, standard error, and return code.

The server is packaged as a Docker image.

## Features

* **MCP Compliant:** Adheres to the Model Context Protocol for seamless integration.
* **Command Execution:** Executes arbitrary shell commands, capturing their output (stdout, stderr) and return code.
* **Standardized API:** Exposes functionality through the `tools/call` MCP method.
* **Dockerized:** Includes a Dockerfile for easy containerization, deployment, and testing.
* **Comprehensive Error Handling:** Returns structured JSON-RPC errors for invalid inputs or execution issues.

## Prerequisites

* Docker
* `bash` (for running helper scripts)
* Python 3.12 (for understanding the code, not strictly for running if using Docker for everything)

## Setup and Installation

### 1. Clone the Repository (if applicable)

If this project is in a Git repository, clone it:
```bash
git clone <repository-url>
cd shell-mcp-server
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
This script will ensure the image is built, start the server in a Docker container, and check its status. The server listens on port 8080 by default (as per the scripts, not 8000).

You can also mount host directories into the container using the `-v` or `--volume` option:
```bash
./start-mcp-server.sh -v /path/on/host:/path/in/container
# Example: Mount current directory's 'data' subfolder to /app/data in container
./start-mcp-server.sh -v "$(pwd)/data:/app/data"
```

## Usage

The Shell MCP Server exposes its functionality via MCP. An MCP client (e.g., an LLM host application) would interact with it as follows:

1.  **Initialize Connection:** The client establishes a connection with the server (running in Docker).
2.  **Tool Discovery (Optional but Recommended):** The client sends a `tools/list` request.
3.  **Tool Invocation:** The client sends a `tools/call` request to use the `shell_tool`.

    **Request:**
    The `shell_tool` accepts a `command` (string, required) and an optional `working_dir` (string).
    If `working_dir` is provided, the command will be executed in that directory inside the container.

    *Basic command:*
    ```json
    {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "shell_tool",
            "arguments": {
                "command": "ls -l /app"
            }
        },
        "id": "request-id-123"
    }
    ```

    *Command with a working directory:*
    ```json
    {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "shell_tool",
            "arguments": {
                "command": "ls -l",
                "working_dir": "/tmp"
            }
        },
        "id": "request-id-456"
    }
    ```

    **Successful Response (Example):**
    ```json
    {
        "jsonrpc": "2.0",
        "result": {
            "stdout": "total 0\n-rw-r--r-- 1 user user 0 Mar 15 10:00 myfile.txt",
            "stderr": "",
            "returncode": 0
        },
        "id": "request-id-123"
    }
    ```

### Testing with `test-mcp-client.sh`

A simple CLI client script is provided to test the running server. Make sure the server is running via `./start-mcp-server.sh`.

```bash
./test-mcp-client.sh list
```

To call the `shell_tool`:
```bash
# Simple command
./test-mcp-client.sh call "echo hello from readme"

# Command with a working directory
./test-mcp-client.sh call -w /tmp "pwd && ls -l"

# Command with working directory and custom server URL
./test-mcp-client.sh call --cwd /app "ls -l src" http://localhost:8080
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
