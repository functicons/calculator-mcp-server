
# Shell MCP Server - Developer Guide

This guide provides detailed information for developers contributing to or maintaining the Shell MCP Server project.

## Table of Contents

1.  [Introduction](#1-introduction)
2.  [Development Environment Setup](#2-development-environment-setup)
3.  [Project Structure Deep Dive](#3-project-structure-deep-dive)
4.  [Core Logic: Shell Command Execution](#4-core-logic-shell-command-execution)
5.  [MCP Server Implementation: `shell_server.py`](#5-mcp-server-implementation-shell_serverpy)
6.  [Error Handling](#6-error-handling)
7.  [Testing Strategy](#7-testing-strategy)
    * [Running Tests with Docker](#running-tests-with-docker)
    * [Manual Testing with `test-mcp-client.sh`](#manual-testing-with-test-mcp-clientsh)
8.  [Dockerization Details](#8-dockerization-details)
9.  [Coding Standards and Conventions](#9-coding-standards-and-conventions)
10. [Dependencies](#10-dependencies)
11. [Troubleshooting](#11-troubleshooting)

## 1. Introduction

The Shell MCP Server is built using Python and the `mcp` SDK (`FastMCP`). It executes shell commands, exposing this functionality via the Model Context Protocol. All execution, including testing, is primarily managed through Docker.

## 2. Development Environment Setup

* **Primary Tool:** Docker. Ensure Docker is installed and running.
* **Code Editor/IDE:** Any preferred editor (VS Code, PyCharm, etc.).
* **Local Python Environment (Optional):** For linting, type checking, and IDE features, you can set up a local Python 3.12 virtual environment:
    ```bash
    python3.12 -m venv venv
    source venv/bin/activate  # Linux/macOS
    # venv\Scripts\activate    # Windows
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    ```
    Remember that `./run-tests.sh` and `./start-mcp-server.sh` will use Docker, not this local environment, for execution.
    The server start scripts (`./start-mcp-server.sh` and `./start-mcp-server-with-inspector.sh`) also support `-v` or `--volume` options to mount host directories into the container, which can be useful for development (e.g., mounting test data or scripts). Example: `./start-mcp-server.sh -v $(pwd)/data:/app/data`.

## 3. Project Structure Deep Dive
(Refer to README.md for the structure diagram)

The `Dockerfile` is configured to build an image containing the application, its dependencies, the test suite, and development dependencies required for testing.

## 4. Core Logic: Shell Command Execution

The core logic for executing shell commands resides within the `shell_tool` method in `src/shell_server.py`.
It utilizes Python's `subprocess.run()` function to execute the provided command string.
The `shell_tool` accepts two arguments:
- `command` (string, required): The shell command to execute.
- `working_dir` (string, optional): If provided, this path is used as the current working directory (`cwd`) for the command execution within the container.

Key aspects of `subprocess.run()` usage:
- `shell=True`: This argument is used to allow shell features like pipes and wildcards in commands. It's important to be aware of the security implications. For this server's purpose, it's assumed that the LLM or its host application provides vetted commands.
- `capture_output=True`: This ensures that `stdout` and `stderr` from the command are captured.
- `text=True`: This decodes `stdout` and `stderr` as strings.
- `cwd=working_dir`: If `working_dir` is supplied to `shell_tool`, it's passed to `subprocess.run()`.
The tool captures and returns the `stdout`, `stderr`, and `returncode` of the executed command.

## 5. MCP Server Implementation: `shell_server.py`

Uses `FastMCP`. The `shell_tool` is defined with `@mcp.tool()` and now accepts an optional `working_dir` argument in addition to the `command`. Type hints and docstrings are vital.
The `FastMCP` instance is initialized with `host` and `port` arguments read from environment variables (`HOST`, `PORT`).
The `mcp.run(transport="streamable-http")` call then starts the server using these configurations. The MCP endpoint for `streamable-http` is typically the root path (`/`).

## 6. Error Handling

Uses standard JSON-RPC 2.0 error objects.
- If the input `command` or `working_dir` (if provided) is not a string, a standard FastMCPError for invalid parameters (`-32602`) is raised.
- If a provided `working_dir` is not found or is not a directory, a `FastMCPError` with code `-32002` ("Working directory not found or invalid") is raised.
- If `subprocess.run()` encounters other issues during command execution, or if any other unexpected Python exception occurs within the tool, a generic `FastMCPError` with code `-32000` is raised, including details about the command and the error.
- The `shell_tool` itself returns the `returncode` from the command, allowing clients to handle non-zero return codes (indicating command errors) as part of the successful tool execution result.

## 7. Testing Strategy

### Running Tests with Docker
All unit tests are executed inside a Docker container to ensure a consistent testing environment.

The `./run-tests.sh` script handles the workflow:
1.  It first calls `./build-image.sh` to ensure the Docker image (`shell-mcp-server:latest`) is built and up-to-date. This image includes `pytest` and all test files.
2.  Then, it runs `python3 -m pytest tests/` inside a new, temporary container based on the image.

To run tests:
```bash
./run-tests.sh
```

### Manual Testing with `test-mcp-client.sh`
This `curl`-based script sends `tools/call` requests to a *running* Shell MCP server instance (started via `./start-mcp-server.sh`). It supports the `shell_tool` including the optional working directory.

**Usage:**
```bash
./test-mcp-client.sh call [-w <dir> | --cwd <dir>] <command_string> [server_url]
```
**Examples:**
```bash
# Simple call
./test-mcp-client.sh call "pwd"

# Call with working directory
./test-mcp-client.sh call -w /tmp "pwd && touch test_file.txt && ls -l test_file.txt"
```
The script uses `curl` and attempts to parse Server-Sent Event (SSE) formatted responses or plain JSON.

## 8. Dockerization Details
The `Dockerfile`:
* Uses `python:3.12-slim`.
* Sets `ENV HOST 0.0.0.0` and `ENV PORT 8080`.
* Installs dependencies from `requirements.txt` and `requirements-dev.txt` using `python3 -m pip`.
* Includes diagnostic steps like `RUN python3 -c "from mcp.server.fastmcp.exceptions import FastMCPError; print(...)"` and `RUN python3 -m pytest --version` to verify installations during build.
* Copies `src/` (application code) and `tests/` (test code).
* Sets `ENV PYTHONPATH "${PYTHONPATH}:/app:/app/src"` to help with module resolution.
* The default `CMD` is `["python3", "src/shell_server.py"]`.
* For testing, `./run-tests.sh` effectively uses the image's Python environment to run `python3 -m pytest tests/`.

## 9. Coding Standards and Conventions
* PEP 8 for Python.
* Mandatory type hints.
* Clear docstrings (PEP 257).

## 10. Dependencies
* **Production (`requirements.txt`):** `mcp`
* **Development (`requirements-dev.txt`):** `pytest` (and linters/formatters if added)

## 11. Troubleshooting
* **Docker Build Issues:** Check `Dockerfile` syntax and base image availability. The diagnostic steps in the Dockerfile can help pinpoint installation issues early.
* **Server Not Starting in Docker:** Use `docker logs shell-mcp-server` (or the container name/ID, e.g., `mcp-shell-inspector` for the inspector version). Check if the `HOST` and `PORT` environment variables are correctly used by the server and if the `FastMCP` constructor and `mcp.run()` call are correct for `streamable-http`.
* **Tests Failing in Docker:**
    * The output from `./run-tests.sh` will show `pytest` output.
    * An `ImportError` during tests usually means a module or its dependency isn't found. Check `PYTHONPATH` in the Dockerfile and `sys.path` modifications in test files. Ensure all necessary packages are in `requirements.txt` or `requirements-dev.txt`.
* **`./test-mcp-client.sh` Issues:** Verify the server is running (`./start-mcp-server.sh`) and accessible on `localhost:8080` (or the configured port). The script now shows raw `curl` output and HTTP status for better debugging. Ensure the `MCP_ENDPOINT_PATH` in the script (defaulting to `/mcp`) is correct.
