# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# Adding /app and /app/src to PYTHONPATH can help with module resolution.
ENV PYTHONPATH "${PYTHONPATH}:/app:/app/src"
ENV HOST 0.0.0.0
ENV PORT 8080
ENV INSPECTOR_PORT 6274
ENV NODE_VERSION 23.x

# Set the working directory in the container
WORKDIR /app

# Install system dependencies, including curl and gnupg for NodeSource
RUN apt-get update && \
    apt-get install -y curl gnupg apt-transport-https ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Install Node.js and npm (which includes npx)
RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION} | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Globally install the MCP Inspector using npm
# This makes it available for `mcp dev --inspector` without npx needing to fetch it.
RUN npm install -g @modelcontextprotocol/inspector

# Copy the requirements files into the container at /app
COPY requirements.txt .
COPY requirements-dev.txt .

# Upgrade pip and install Python dependencies
# Using python3 -m pip for consistency
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --no-cache-dir -r requirements.txt
RUN python3 -m pip install --no-cache-dir -r requirements-dev.txt

# Diagnostic steps
RUN python3 -c "from mcp.server.fastmcp.exceptions import FastMCPError; print('MCP SDK FastMCPError import successful')"
RUN python3 -m pytest --version
RUN node --version
RUN npm --version
RUN npx --version
# Check if mcp-inspector command is available after global npm install
RUN if command -v mcp-inspector &> /dev/null; then mcp-inspector --version; else echo "mcp-inspector command not directly found, relying on mcp dev to launch."; fi


# Copy the application source code and test code into the container
COPY src/ src/
COPY tests/ tests/

# Expose the port the app runs on (defined by ENV PORT)
EXPOSE ${PORT}
# Expose the port for the MCP Inspector
EXPOSE ${INSPECTOR_PORT}

# Define the command to run the application (when not running tests)
# This is for the default streamable-http mode.
# For inspector mode, the command will be overridden in start-mcp-server-with-inspector.sh
CMD ["python3", "src/calculator_server.py"]
