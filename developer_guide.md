
# Calculator MCP Server - Developer Guide

This guide provides detailed information for developers contributing to or maintaining the Calculator MCP Server project.

## Table of Contents

1.  [Introduction](#1-introduction)
2.  [Development Environment Setup](#2-development-environment-setup)
3.  [Project Structure Deep Dive](#3-project-structure-deep-dive)
4.  [Core Logic: `safe_eval.py`](#4-core-logic-safe_evalpy)
5.  [MCP Server Implementation: `calculator_server.py`](#5-mcp-server-implementation-calculator_serverpy)
6.  [Error Handling](#6-error-handling)
7.  [Testing Strategy](#7-testing-strategy)
    * [Running Tests with Docker](#running-tests-with-docker)
    * [Manual Testing with `test-mcp-client.sh`](#manual-testing-with-test-mcp-clientsh)
8.  [Dockerization Details](#8-dockerization-details)
9.  [Coding Standards and Conventions](#9-coding-standards-and-conventions)
10. [Dependencies](#10-dependencies)
11. [Troubleshooting](#11-troubleshooting)

## 1. Introduction

The Calculator MCP Server is built using Python and the `mcp` SDK (`FastMCP`). It evaluates arithmetic expressions safely, exposing this functionality via the Model Context Protocol. All execution, including testing, is primarily managed through Docker.

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

## 3. Project Structure Deep Dive
(Refer to README.md for the structure diagram)

The `Dockerfile` is configured to build an image containing the application, its dependencies, the test suite, and development dependencies required for testing.

## 4. Core Logic: `safe_eval.py`

This module safely parses and evaluates arithmetic expressions. It avoids Python's `eval()` for security. It supports basic operations (+, -, *, /), parentheses, and operator precedence.

## 5. MCP Server Implementation: `calculator_server.py`

Uses `FastMCP`. The `calculator_tool` is defined with `@mcp.tool()`. Type hints and docstrings are vital. 
The `FastMCP` instance is initialized with `host` and `port` arguments read from environment variables (`HOST`, `PORT`).
The `mcp_server.run(transport="streamable-http")` call then starts the server using these configurations. The MCP endpoint for `streamable-http` is typically the root path (`/`).

## 6. Error Handling

Uses standard JSON-RPC 2.0 error objects. Custom error codes:
* **`-32000`**: Invalid arithmetic expression.
* **`-32001`**: Division by zero.

## 7. Testing Strategy

### Running Tests with Docker
All unit tests are executed inside a Docker container to ensure a consistent testing environment.

The `./run-tests.sh` script handles the workflow:
1.  It first calls `./build-image.sh` to ensure the Docker image (`calculator-mcp-server:latest`) is built and up-to-date. This image includes `pytest` and all test files.
2.  Then, it runs `python3 -m pytest tests/` inside a new, temporary container based on the image.

To run tests:
```bash
./run-tests.sh
```

### Manual Testing with `test-mcp-client.sh`
This `curl`-based script sends `tools/call` requests to a *running* Calculator MCP server instance (started via `./start-mcp-server.sh`). It uses the `-L` flag to follow redirects and an appropriate `Accept` header. It also attempts to parse Server-Sent Event (SSE) formatted responses.

## 8. Dockerization Details
The `Dockerfile`:
* Uses `python:3.12-slim`.
* Sets `ENV HOST 0.0.0.0` and `ENV PORT 8000`.
* Installs dependencies from `requirements.txt` and `requirements-dev.txt` using `python3 -m pip`.
* Includes diagnostic steps like `RUN python3 -c "from mcp.server.fastmcp.exceptions import FastMCPError; print(...)"` and `RUN python3 -m pytest --version` to verify installations during build.
* Copies `src/` (application code) and `tests/` (test code).
* Sets `ENV PYTHONPATH "${PYTHONPATH}:/app:/app/src"` to help with module resolution.
* The default `CMD` is `["python3", "src/calculator_server.py"]`.
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
* **Server Not Starting in Docker:** Use `docker logs mcp-calculator` (or the container name/ID). Check if the `HOST` and `PORT` environment variables are correctly used by the server and if the `FastMCP` constructor and `mcp_server.run()` call are correct for `streamable-http`.
* **Tests Failing in Docker:**
    * The output from `./run-tests.sh` will show `pytest` output.
    * An `ImportError` during tests usually means a module or its dependency isn't found. Check `PYTHONPATH` in the Dockerfile and `sys.path` modifications in test files. Ensure all necessary packages are in `requirements.txt` or `requirements-dev.txt`.
* **`./test-mcp-client.sh` Issues:** Verify the server is running (`./start-mcp-server.sh`) and accessible on `localhost:8000`. The script now shows raw `curl` output and HTTP status for better debugging. If you see a 307 redirect, ensure the `MCP_ENDPOINT_PATH` in the script (defaulting to empty for root `/`) is correct for your server. A 406 error means the `Accept` header is incorrect.
