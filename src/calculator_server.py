
import logging
import os 
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import FastMCPError 

from safe_eval import (
    safe_evaluate_expression, SafeEvalError, DivisionByZeroError, 
    InvalidExpressionError, UnbalancedParenthesesError, UnknownCharacterError
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Read HOST and PORT from environment variables for FastMCP constructor
# These are set in the Dockerfile. Uvicorn (used by FastMCP for streamable-http)
# will also pick these up if FastMCP passes them or by default.
APP_HOST = os.environ.get("HOST", "0.0.0.0")
APP_PORT = int(os.environ.get("PORT", 8000))
logger.info(f"FastMCP configured with host={APP_HOST}, port={APP_PORT}.")

mcp = FastMCP(
    "CalculatorServer", 
    stateless_http=True,
    host=APP_HOST, 
    port=APP_PORT
)

ERROR_INVALID_ARITHMETIC_EXPRESSION = -32000
ERROR_DIVISION_BY_ZERO = -32001

@mcp.tool()
def calculator_tool(expression: str) -> dict:
    """
    Performs arithmetic calculations on the input expression string.
    Supports addition (+), subtraction (-), multiplication (*), and division (/).
    Handles parentheses for grouping and respects operator precedence.
    Input: A string like '5*3-2/4' or '3.8 - 3.11'.
    Output: A dictionary with the numerical result under the 'value' key, e.g., {"value": 14.5}.
    Handles potential errors such as invalid expressions or division by zero.
    """
    logger.info(f"Calculator tool called with expression: \"{expression}\"")

    if not isinstance(expression, str):
        logger.error("Expression is not a string.")
        raise FastMCPError("Invalid input: expression must be a string.", -32602, {"input_expression": str(expression)})
    try:
        result = safe_evaluate_expression(expression)
        logger.info(f"Expression \"{expression}\" evaluated to: {result}")
        return {"value": float(result)}
    except DivisionByZeroError as e:
        logger.warning(f"Division by zero: \"{expression}\". Error: {e}")
        raise FastMCPError(str(e), ERROR_DIVISION_BY_ZERO, {"input_expression": expression})
    except (InvalidExpressionError, UnbalancedParenthesesError, UnknownCharacterError) as e: 
        logger.warning(f"Invalid expression: \"{expression}\". Error: {e}")
        raise FastMCPError(str(e), ERROR_INVALID_ARITHMETIC_EXPRESSION, {"input_expression": expression})
    except SafeEvalError as e: 
        logger.error(f"Evaluation error for \"{expression}\": {e}")
        raise FastMCPError(str(e), ERROR_INVALID_ARITHMETIC_EXPRESSION, {"input_expression": expression})
    except Exception as e: 
        logger.error(f"Unexpected error for \"{expression}\": {e}", exc_info=True)
        raise FastMCPError("An unexpected internal error occurred.", -32603, {"input_expression": expression, "error_details": str(e)})

if __name__ == "__main__":
    logger.info(f"Attempting to start Calculator MCP Server using streamable-http transport...")
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
