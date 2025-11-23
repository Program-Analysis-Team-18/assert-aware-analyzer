"""Assertion Solver using Z3 library."""
from dataclasses import dataclass
from typing import Any
from tree_sitter import Node
import z3
from .utils import translate_expression


@dataclass
class SolveResult:
    """Container for solver output."""
    status: z3.CheckSatResult
    variables: dict[str, Any]
    solver: z3.Solver
    model: z3.ModelRef | None


class AssertSolver:
    """Translates Java assert statements into Z3 constraints and finds models."""

    def __init__(self, assert_nodes: list[Node]):
        self.assert_nodes = assert_nodes
        self.variables: dict[str, Any] = {}
        self.solver = z3.Solver()

    def _extract_expression_node(self, assert_node: Node) -> Node | None:
        """Return the expression part of an `assert` statement."""
        for child in assert_node.children:
            if child.type not in ("assert", ";"):
                return child
        return None

    def _add_negated_assertions(self):
        """Translate all assert nodes and add negated expressions to solver."""
        for assert_node in self.assert_nodes:
            expr_node = self._extract_expression_node(assert_node)
            if not expr_node:
                continue

            expr = translate_expression(expr_node, self.variables)
            self.solver.add(z3.Not(expr))

    def _block_current_model(self, model: z3.ModelRef, iteration: int):
        """Add a clause to block the current model and force the solver to find a new one."""
        literals = []

        for var in self.variables.values():

            if var.sort().kind() == z3.Z3_INT_SORT and iteration % 2 == 0:
                self.solver.add(var >= 1)

            val = model.evaluate(var, model_completion=True)
            literals.append(var != val)

        if literals:
            self.solver.add(z3.Or(literals))

        return bool(literals)

    def solve(self, attempts: int = 1) -> SolveResult:
        """
        Translate asserts into Z3 expressions, enumerate models, and return the N-th model.

        Example:
        attempts=1 -> return the first model
        attempts=3 -> return the third distinct model
        """
        self._add_negated_assertions()

        last_model = None

        for i in range(attempts):
            result = self.solver.check()

            if result != z3.sat:
                return SolveResult(
                    status=result,
                    variables=self.variables,
                    solver=self.solver,
                    model=None
                )

            model = self.solver.model()

            # If this is the model we want, return it
            if i == attempts - 1:
                return SolveResult(
                    status=result,
                    variables=self.variables,
                    solver=self.solver,
                    model=model
                )

            # Otherwise block the current model and continue
            has_vars = self._block_current_model(model, i)

            # No new distinct model exists
            if not has_vars:
                return SolveResult(
                    status=result,
                    variables=self.variables,
                    solver=self.solver,
                    model=model
                )

            last_model = model

        return SolveResult(
            status=result,
            variables=self.variables,
            solver=self.solver,
            model=last_model
        )
