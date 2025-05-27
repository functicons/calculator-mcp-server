
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from mcp.server.fastmcp.exceptions import FastMCPError 
from calculator_server import (
    calculator_tool, ERROR_INVALID_ARITHMETIC_EXPRESSION, ERROR_DIVISION_BY_ZERO
)


VALID_TOOL_CALLS = [("1 + 1", 2.0), ("-5.5 * 2", -11.0), ("(5-3)*8/4", 4.0)]

@pytest.mark.parametrize("expression, expected_value", VALID_TOOL_CALLS)
def test_calculator_tool_valid(expression, expected_value):
    result = calculator_tool(expression=expression)
    assert "value" in result
    assert isinstance(result["value"], float)
    assert abs(result["value"] - expected_value) < 1e-9, f"Failed on: {expression}"

ERROR_TOOL_CALLS = [
    ("1 / 0", ERROR_DIVISION_BY_ZERO, "division by zero"),
    ("1 +", ERROR_INVALID_ARITHMETIC_EXPRESSION, "Invalid RPN expression"), 
    ("1 % 2", ERROR_INVALID_ARITHMETIC_EXPRESSION, "Unknown character"),
    ("()", ERROR_INVALID_ARITHMETIC_EXPRESSION, "empty RPN") 
]

@pytest.mark.parametrize("expression, err_code, msg_sub", ERROR_TOOL_CALLS)
def test_calculator_tool_errors(expression, err_code, msg_sub):
    with pytest.raises(FastMCPError) as excinfo: 
        calculator_tool(expression=expression)
    
    # Accessing error details from excinfo.value.args
    # args[0] is message, args[1] is code, args[2] is data (if present)
    assert excinfo.value.args[1] == err_code, f"Failed on: {expression}. Expected code {err_code}, got {excinfo.value.args[1]}"
    assert msg_sub.lower() in excinfo.value.args[0].lower(), f"Failed on: {expression}, Message: '{excinfo.value.args[0]}' did not contain '{msg_sub}'"
    
    assert len(excinfo.value.args) > 2, f"FastMCPError for '{expression}' missing data argument."
    error_data = excinfo.value.args[2]
    assert error_data is not None, f"FastMCPError data should not be None for '{expression}'."
    assert error_data.get("input_expression") == expression, f"FastMCPError data mismatch for '{expression}'."


def test_calculator_tool_non_string():
    with pytest.raises(FastMCPError) as excinfo: 
        calculator_tool(expression=123) # type: ignore
    assert excinfo.value.args[1] == -32602 
    assert "expression must be a string" in excinfo.value.args[0].lower()
