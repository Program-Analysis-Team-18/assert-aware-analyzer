"""Utils for the Assertion Solver package based on Z3 library."""
from tree_sitter import Node
from z3 import Int, RealVal, And, Or, Not


# def node_text(node, code_bytes):
#     """Return the source text for a Tree-sitter node."""
#     return code_bytes[node.start_byte:node.end_byte].decode("utf8")

def node_text(node: Node):
    """Return the source text for a Tree-sitter node."""
    # assert str(node.text)[2:-1] == node.text.decode(), f"{str(node.text)[2:-1]} != {node.text.decode()}"
    return node.text.decode()

def translate_expression(node: Node, variables):
    """Recursively translate a Tree-sitter expression node into a Z3 expression."""
    t = node.type
    var_name = node_text(node).strip()

    if t.endswith("_literal"):
        try:
            return int(var_name)
        except ValueError:
            return RealVal(var_name)

    if t in ("identifier", "method_invocation"):
        if var_name not in variables:
            variables[var_name] = Int(var_name)
        return variables[var_name]

    if t == "parenthesized_expression":
        return translate_expression(node.children[1], variables)

    if t == "unary_expression":
        op = node.children[0]
        operand = node.children[1]
        if node_text(op) == "!":
            return Not(translate_expression(operand, variables))
        raise ValueError(
            f"Unhandled unary operator: {node_text(op)}")

    if t == "binary_expression":
        left, op, right = node.children
        l = translate_expression(left, variables)
        r = translate_expression(right, variables)
        op_text = node_text(op)

        match op_text:
            case "+": expr = l + r
            case "-": expr = l - r
            case "*": expr = l * r
            case "/": expr = l / r
            case ">": expr = l > r
            case ">=": expr = l >= r
            case "<": expr = l < r
            case "<=": expr = l <= r
            case "==": expr = l == r
            case "!=": expr = l != r
            case "%": expr = l % r
            case "&&": expr = And(l, r)
            case "||": expr = Or(l, r)
            case _:
                raise ValueError(f"Unhandled binary operator: {op_text}")
        return expr

    raise ValueError(f"Unhandled node type: {t} with text: {var_name}")
