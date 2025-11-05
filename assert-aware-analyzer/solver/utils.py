"""Utils for the Assertion Solver package based on Z3 library."""
from z3 import Int, RealVal, And, Or, Not


def node_text(node, code_bytes):
    """Return the source text for a Tree-sitter node."""
    return code_bytes[node.start_byte:node.end_byte].decode("utf8")


def translate_expression(node, code_bytes, variables):
    """
    Recursively translate a Tree-sitter expression node into a Z3 expression.
    Handles arithmetic, relational, and logical operators.
    """
    t = node.type
    var_name = node_text(node, code_bytes).strip()

    # Numeric literal
    if t.endswith("_literal"):
        try:
            return int(var_name)
        except ValueError:
            return RealVal(var_name)

    # Variable or method call
    if t in ("identifier", "method_invocation"):
        if var_name not in variables:
            variables[var_name] = Int(var_name)
        return variables[var_name]

    # Parenthesized expression
    if t == "parenthesized_expression":
        return translate_expression(node.children[1], code_bytes, variables)

    # Unary (handle '!')
    if t == "unary_expression":
        op = node.children[0]
        operand = node.children[1]
        if node_text(op, code_bytes) == "!":
            return Not(translate_expression(operand, code_bytes, variables))
        raise ValueError(
            f"Unhandled unary operator: {node_text(op, code_bytes)}")

    # Binary (arithmetic, relational, logical)
    if t == "binary_expression":
        left, op, right = node.children
        l = translate_expression(left, code_bytes, variables)
        r = translate_expression(right, code_bytes, variables)
        op_text = node_text(op, code_bytes)

        # Arithmetic
        if op_text == "+":
            return l + r
        if op_text == "-":
            return l - r
        if op_text == "*":
            return l * r
        if op_text == "/":
            return l / r

        # Relational
        if op_text == ">":
            return l > r
        if op_text == ">=":
            return l >= r
        if op_text == "<":
            return l < r
        if op_text == "<=":
            return l <= r
        if op_text == "==":
            return l == r
        if op_text == "!=":
            return l != r

        # Logical
        if op_text == "&&":
            return And(l, r)
        if op_text == "||":
            return Or(l, r)

    raise ValueError(f"Unhandled node type: {t} with text: {var_name}")
