
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from safe_eval import (
    safe_evaluate_expression, SafeEvalError, InvalidExpressionError,
    DivisionByZeroError, UnbalancedParenthesesError, UnknownCharacterError
)


VALID_EXPRESSIONS = [
    ("1 + 1", 2.0), ("(2 + 3) * 4", 20.0), ("-1", -1.0), ("10.5 + 2.5", 13.0),
    ("1/3", 1/3), ("  1 +   1  ", 2.0), (".5 + .5", 1.0), ("5.", 5.0),
    ("5*-2", -10.0), ("1 - -1", 2.0), ("123", 123.0), ("-10 / -2", 5.0),
    ("0.0", 0.0), ("-0.0", 0.0)
]

@pytest.mark.parametrize("expression, expected", VALID_EXPRESSIONS)
def test_valid_expressions(expression, expected):
    assert abs(safe_evaluate_expression(expression) - expected) < 1e-9, f"Failed on: {expression}"

INVALID_EXPRESSIONS_AND_ERRORS = [
    ("1 / 0", DivisionByZeroError), 
    ("1 +", InvalidExpressionError), 
    ("(1 + 2", UnbalancedParenthesesError), 
    ("1 @ 2", UnknownCharacterError),
    ("", InvalidExpressionError), 
    ("  ", InvalidExpressionError), 
    ("abc + 1", UnknownCharacterError),
    ("1 + ( )", InvalidExpressionError), 
    ("()", InvalidExpressionError), 
    ("1.2.3", InvalidExpressionError), 
    ("1+", InvalidExpressionError), 
    ("*1", InvalidExpressionError), 
    ("1 2", InvalidExpressionError), 
]

@pytest.mark.parametrize("expression, error_type", INVALID_EXPRESSIONS_AND_ERRORS)
def test_invalid_expressions(expression, error_type):
    with pytest.raises(error_type): 
        safe_evaluate_expression(expression)

def test_non_string_input():
    with pytest.raises(TypeError):
        safe_evaluate_expression(123) # type: ignore
    with pytest.raises(TypeError):
        safe_evaluate_expression(None) # type: ignore
    with pytest.raises(TypeError):
        safe_evaluate_expression([1, "+", 1]) # type: ignore
