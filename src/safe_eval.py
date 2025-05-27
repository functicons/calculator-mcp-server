
import re
import operator

# --- Custom Exceptions ---
class SafeEvalError(Exception):
    """Base class for errors during safe evaluation."""
    pass

class InvalidExpressionError(SafeEvalError):
    """Raised for malformed or unsupported expressions."""
    pass

class DivisionByZeroError(SafeEvalError):
    """Raised when division by zero is attempted."""
    pass

class UnbalancedParenthesesError(InvalidExpressionError):
    """Raised for mismatched parentheses."""
    pass

class UnknownCharacterError(InvalidExpressionError):
    """Raised for unknown characters in the expression."""
    pass


# --- Tokenizer ---
def tokenize(expression: str) -> list:
    """
    Converts an infix expression string into a list of tokens (numbers, operators, parentheses).
    Skips whitespace.
    """
    token_specification = [
        ('NUMBER',   r'(?:\d+(?:\.\d*)?|\.\d+)'), 
        ('OPERATOR', r'[+\-*/()]'),              
        ('SPACE',    r'\s+'), 
        ('MISMATCH', r'.'),                       
    ]
    tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
    tokens = []
    current_pos = 0
    while current_pos < len(expression):
        mo = re.match(tok_regex, expression[current_pos:])
        
        if not mo:
            raise InvalidExpressionError(f"Unable to tokenize expression at: '{expression[current_pos:]}'")

        kind = mo.lastgroup
        value = mo.group()
        
        if kind == 'NUMBER':
            try:
                tokens.append(float(value))
            except ValueError:
                raise InvalidExpressionError(f"Invalid number format '{value}' at position {current_pos}.")
        elif kind == 'OPERATOR':
            tokens.append(value)
        elif kind == 'SPACE':
            pass 
        elif kind == 'MISMATCH':
            raise UnknownCharacterError(f"Unknown character '{value}' in expression at position {current_pos}.")
        
        current_pos += len(value) 
        
    return tokens


# --- Shunting-yard algorithm for Infix to RPN (Reverse Polish Notation) ---
PRECEDENCE = {'+': 1, '-': 1, '*': 2, '/': 2}
ASSOCIATIVITY = {'+': 'L', '-': 'L', '*': 'L', '/': 'L'}

def infix_to_rpn(tokens: list) -> list:
    """
    Converts a list of infix tokens to RPN, handling unary operators.
    """
    output_queue = []
    operator_stack = []
    processed_tokens = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        is_unary = False
        if token in ('+', '-') and \
           (i == 0 or (isinstance(tokens[i-1], str) and tokens[i-1] in ('(', '+', '-', '*', '/'))):
            if i + 1 < len(tokens) and isinstance(tokens[i+1], (int, float)):
                is_unary = True
        
        if is_unary:
            if token == '-':
                processed_tokens.append(-tokens[i+1])
            else: # token == '+'
                processed_tokens.append(tokens[i+1])
            i += 1 
        else:
            processed_tokens.append(token)
        i += 1
    tokens = processed_tokens

    for token in tokens:
        if isinstance(token, (int, float)):
            output_queue.append(token)
        elif token in PRECEDENCE: 
            while (operator_stack and operator_stack[-1] != '(' and
                   (PRECEDENCE.get(operator_stack[-1], 0) > PRECEDENCE[token] or
                    (PRECEDENCE.get(operator_stack[-1], 0) == PRECEDENCE[token] and ASSOCIATIVITY[token] == 'L'))):
                output_queue.append(operator_stack.pop())
            operator_stack.append(token)
        elif token == '(':
            operator_stack.append(token)
        elif token == ')':
            while operator_stack and operator_stack[-1] != '(':
                output_queue.append(operator_stack.pop())
            if not operator_stack or operator_stack[-1] != '(':
                raise UnbalancedParenthesesError("Mismatched or missing left parenthesis.")
            operator_stack.pop() 
        else:
            raise InvalidExpressionError(f"Unknown token during RPN conversion: {token}")

    while operator_stack:
        if operator_stack[-1] == '(':
            raise UnbalancedParenthesesError("Mismatched or missing right parenthesis.")
        output_queue.append(operator_stack.pop())
    return output_queue


# --- RPN Evaluator ---
OPERATORS = {'+': operator.add, '-': operator.sub, '*': operator.mul, '/': operator.truediv}

def evaluate_rpn(rpn_tokens: list) -> float:
    """Evaluates an expression in RPN."""
    operand_stack = []
    for token in rpn_tokens:
        if isinstance(token, (int, float)):
            operand_stack.append(token)
        elif token in OPERATORS:
            if len(operand_stack) < 2:
                raise InvalidExpressionError("Invalid RPN expression: not enough operands for operator.")
            op2 = operand_stack.pop()
            op1 = operand_stack.pop()
            if token == '/' and op2 == 0:
                raise DivisionByZeroError("Division by zero in expression.")
            try:
                result = OPERATORS[token](op1, op2)
                operand_stack.append(result)
            except Exception as e: 
                raise SafeEvalError(f"Error during operation {op1} {token} {op2}: {e}")
        else:
            raise InvalidExpressionError(f"Unknown token in RPN expression: {token}")

    if len(operand_stack) != 1:
        raise InvalidExpressionError(f"Invalid RPN expression: stack should have 1 result, has {len(operand_stack)}. Original RPN: {rpn_tokens}")
    
    return operand_stack[0]


# --- Main Safe Evaluation Function ---
def safe_evaluate_expression(expression: str) -> float:
    """Safely evaluates an arithmetic string expression."""
    if not isinstance(expression, str):
        raise TypeError("Expression must be a string.")
    
    stripped_expression = expression.strip()
    if not stripped_expression:
        raise InvalidExpressionError("Expression cannot be empty or just whitespace.")
    
    try:
        tokens = tokenize(stripped_expression) 
        
        if not tokens: 
             raise InvalidExpressionError("Expression contains no evaluable tokens after tokenization (e.g. only operators/parentheses that were consumed by RPN logic without numbers).")
        
        rpn_expression = infix_to_rpn(tokens)
        
        if not rpn_expression:
            if any(isinstance(t, (int,float)) for t in tokens): 
                 raise InvalidExpressionError("Expression with numbers resulted in empty RPN (e.g. '5 ()').")
            else: 
                 raise InvalidExpressionError("Expression results in empty RPN or has no evaluable content (e.g. '()', '(+)', or empty/whitespace).")

        result = evaluate_rpn(rpn_expression)
        return float(result) 
    except SafeEvalError: 
        raise
    except Exception as e:
        raise SafeEvalError(f"An unexpected error occurred during evaluation: {type(e).__name__} - {e}")

