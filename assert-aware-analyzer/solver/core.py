"""Assertion Solver using Z3 library."""
from z3 import Solver, Not
from .utils import translate_expression


class AssertSolver:
    """Handles the translation of Java assert statements into Z3 constraints."""

    def __init__(self, assert_nodes, code_bytes):
        """
        :param assert_nodes: list of Tree-sitter nodes of type 'assert_statement'
        :param code_bytes: the original Java source code as bytes
        """
        self.assert_nodes = assert_nodes
        self.code_bytes = code_bytes
        self.variables = {}
        self.solver = Solver()

    def _extract_expression_node(self, assert_node):
        """Skip the 'assert' keyword and ';' symbol to extract the expression node."""
        for child in assert_node.children:
            if child.type not in ("assert", ";"):
                return child
        return None

    def solve(self):  # create object to keep the result
        """Parse all asserts, translate to Z3, and add them to the solver."""
        for assert_node in self.assert_nodes:
            expr_node = self._extract_expression_node(assert_node)
            if not expr_node:
                continue

            expr = translate_expression(
                expr_node, self.code_bytes, self.variables)
            self.solver.add(Not(expr))

        result = self.solver.check()
        model = self.solver.model() if f"{result}" == "sat" else None

        # TODO add all other classifications
        # if result == NOSAT            => contradiction
        # if simplifying left == right  => tautology
        # if result == True             => self implied

        return {
            "status": result,
            "variables": self.variables,
            "solver": self.solver,
            "model": model,
            # add "classification"
        }
