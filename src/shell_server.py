
import logging
import os
import subprocess # Added for shell_tool
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import FastMCPError

# Removed safe_eval imports

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Read HOST and PORT from environment variables for FastMCP constructor
# These are set in the Dockerfile. Uvicorn (used by FastMCP for streamable-http)
# will also pick these up if FastMCP passes them or by default.
APP_HOST = os.environ.get("HOST", "0.0.0.0")
APP_PORT = int(os.environ.get("PORT", 8080))
logger.info(f"FastMCP configured with host={APP_HOST}, port={APP_PORT}.")

mcp = FastMCP(
    "ShellServer",  # Changed server name
    stateless_http=True,
    host=APP_HOST,
    port=APP_PORT
)

# Removed calculator_tool specific error codes
ERROR_INVALID_WORKING_DIR = -32002

@mcp.tool()
def shell_tool(command: str, working_dir: str = None) -> dict:
    """
    Executes a shell command in an optional working directory and returns its output.
    Input:
      command (str): The command to execute.
      working_dir (str, optional): The working directory for the command. Defaults to None (current dir).
    Output: A dictionary with 'stdout', 'stderr', and 'returncode'.
    """
    log_details = [f"command: \"{command}\""]
    if working_dir:
        log_details.append(f"working_dir: \"{working_dir}\"")
    logger.info(f"Shell tool called with {', '.join(log_details)}")

    if not isinstance(command, str):
        logger.error("Command is not a string.")
        raise FastMCPError("Invalid input: command must be a string.", -32602, {"input_command": str(command), "working_dir": working_dir})

    if working_dir is not None and not isinstance(working_dir, str):
        logger.error("Working directory is not a string.")
        raise FastMCPError("Invalid input: working_dir must be a string if provided.", -32602, {"input_command": command, "working_dir": str(working_dir)})

    subprocess_args = {
        "shell": True,
        "capture_output": True,
        "text": True
    }

    if working_dir:
        subprocess_args["cwd"] = working_dir

    try:
        # Execute the command
        result = subprocess.run(command, **subprocess_args)

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        returncode = result.returncode

        log_msg_executed = [f"Command \"{command}\" executed"]
        if working_dir:
            log_msg_executed.append(f"in working_dir \"{working_dir}\"")
        logger.info(f"{''.join(log_msg_executed)}.")

        logger.info(f"  Return Code: {returncode}")
        logger.info(f"  Stdout: \"{stdout}\"")
        logger.info(f"  Stderr: \"{stderr}\"")

        return {
            "stdout": stdout,
            "stderr": stderr,
            "returncode": returncode
        }
    except FileNotFoundError as e:
        logger.warning(f"Working directory not found for command \"{command}\": \"{working_dir}\". Error: {e}")
        raise FastMCPError(
            f"Working directory not found: \"{working_dir}\"",
            ERROR_INVALID_WORKING_DIR,
            {"command": command, "working_dir": working_dir, "error_details": str(e)}
        )
    except NotADirectoryError as e: # Catch if working_dir is a file, not a directory
        logger.warning(f"Specified working_dir is not a directory for command \"{command}\": \"{working_dir}\". Error: {e}")
        raise FastMCPError(
            f"Specified working_dir is not a directory: \"{working_dir}\"",
            ERROR_INVALID_WORKING_DIR,
            {"command": command, "working_dir": working_dir, "error_details": str(e)}
        )
    except Exception as e:
        error_context = {"command": command, "error_details": str(e)}
        if working_dir:
            error_context["working_dir"] = working_dir
        logger.error(f"Error executing command \"{command}\" (working_dir: {working_dir}): {e}", exc_info=True)
        raise FastMCPError(
            f"An unexpected error occurred while executing the command: {str(e)}",
            -32000, # Generic error code for other shell execution errors
            error_context
        )

if __name__ == "__main__":
    logger.info(f"Attempting to start Shell MCP Server using streamable-http transport...")
    try:
        # For streamable-http, FastMCP.run() should not need host/port if they were set in constructor
        # or if it relies purely on Uvicorn's env var handling (HOST, PORT).
        mcp.run(transport="streamable-http")
    except TypeError as te:
        if "unexpected keyword argument 'host'" in str(te) or "unexpected keyword argument 'port'" in str(te):
            logger.warning(f"FastMCP.run() does not accept host/port for streamable-http. Retrying without them, relying on constructor/env vars.")
            try:
                mcp.run(transport="streamable-http") # Try without host/port
            except Exception as e_retry:
                logger.critical(f"Failed to start MCP server on retry: {e_retry}", exc_info=True)
                import sys
                sys.exit(1)
        else:
            logger.critical(f"Failed to start MCP server: {te}", exc_info=True)
            import sys
            sys.exit(1)
    except Exception as e:
        logger.critical(f"Failed to start MCP server: {e}", exc_info=True)
        import sys
        sys.exit(1)
