import jpamb
from jpamb import jvm
from dataclasses import dataclass
import z3
from typing import Iterable

import sys
from loguru import logger
import os

logger.remove()
logger.add(sys.stderr, format="[{level}] {message}")


@dataclass
class PC:
    method: jvm.AbsMethodID
    offset: int

    def __iadd__(self, delta):
        self.offset += delta
        return self

    def __add__(self, delta):
        return PC(self.method, self.offset + delta)

    def __str__(self):
        return f"{self.method}:{self.offset}"


@dataclass
class Bytecode:
    suite: jpamb.Suite
    methods: dict[jvm.AbsMethodID, list[jvm.Opcode]]

    def __getitem__(self, pc: PC) -> jvm.Opcode:
        try:
            opcodes = self.methods[pc.method]
        except KeyError:
            opcodes = list(self.suite.method_opcodes(pc.method))
            self.methods[pc.method] = opcodes
        return opcodes[pc.offset]


@dataclass
class Stack[T]:
    items: list[T]

    def __bool__(self) -> bool:
        return len(self.items) > 0

    @classmethod
    def empty(cls):
        return cls([])

    def peek(self) -> T:
        return self.items[-1]

    def pop(self) -> T:
        return self.items.pop(-1)

    def push(self, value):
        self.items.append(value)
        return self

    def copy(self):
        return Stack(self.items.copy())

    def __str__(self):
        if not self:
            return "ϵ"
        return "".join(f"{v}" for v in self.items)


suite = jpamb.Suite()
bc = Bytecode(suite, dict())


# Symbolic execution types
SymPath = list[z3.ExprRef]  # Path constraints


@dataclass
class SymValue:
    """Represents a symbolic or concrete value"""
    expr: z3.ExprRef | jvm.Value
    
    def is_symbolic(self) -> bool:
        return isinstance(self.expr, z3.ExprRef)
    
    def is_concrete(self) -> bool:
        return isinstance(self.expr, jvm.Value)


@dataclass
class SymState:
    """Symbolic execution state"""
    locals: dict[int, SymValue]
    stack: Stack[SymValue]
    heap: dict[int, SymValue]
    
    @classmethod
    def from_locals(cls, locals_dict: dict[int, z3.ExprRef]):
        """Create symbolic state from symbolic variables"""
        sym_locals = {i: SymValue(expr) for i, expr in locals_dict.items()}
        return cls(sym_locals, Stack.empty(), {})
    
    def copy(self):
        """Deep copy of the state"""
        return SymState(
            self.locals.copy(),
            self.stack.copy(),
            self.heap.copy()
        )


def to_z3_expr(sym_val: SymValue) -> z3.ExprRef:
    """Convert SymValue to Z3 expression"""
    if sym_val.is_symbolic():
        return sym_val.expr
    else:
        # Concrete value - convert to Z3 constant
        val = sym_val.expr
        if val.type == jvm.Int() or val.type == jvm.Boolean():
            return z3.IntVal(val.value)
        else:
            raise NotImplementedError(f"Cannot convert {val.type} to Z3")


def step(pc: PC, state: SymState) -> Iterable[tuple[PC, SymState, SymPath]]:
    """
    Symbolic execution step - returns iterable of (next_pc, next_state, path_constraints)
    Each tuple represents a possible execution path from this instruction.
    """
    opr = bc[pc]
    logger.debug(f"SYM STEP {opr} at {pc}")
    
    match opr:
        case jvm.Push(value=v):
            new_state = state.copy()
            new_state.stack.push(SymValue(v))
            return [(PC(pc.method, pc.offset + 1), new_state, [])]
        
        case jvm.Load(type=jvm.Int(), index=i):
            new_state = state.copy()
            v = state.locals.get(i)
            if v is None:
                raise RuntimeError(f"Local variable {i} not initialized")
            new_state.stack.push(v)
            return [(PC(pc.method, pc.offset + 1), new_state, [])]
        
        case jvm.Binary(type=jvm.Int(), operant=opr_type):
            new_state = state.copy()
            v2 = new_state.stack.pop()
            v1 = new_state.stack.pop()
            
            z3_v1 = to_z3_expr(v1)
            z3_v2 = to_z3_expr(v2)
            
            result_expr = None
            path_constraint = []
            
            match opr_type:
                case jvm.BinaryOpr.Add:
                    result_expr = z3_v1 + z3_v2
                case jvm.BinaryOpr.Sub:
                    result_expr = z3_v1 - z3_v2
                case jvm.BinaryOpr.Mul:
                    result_expr = z3_v1 * z3_v2
                case jvm.BinaryOpr.Div:
                    # Division by zero check - return two paths
                    # Path 1: division by zero error
                    state_error = new_state.copy()
                    path_div_zero = [z3_v2 == 0]
                    
                    # Path 2: successful division
                    state_ok = new_state.copy()
                    result_expr = z3_v1 / z3_v2
                    state_ok.stack.push(SymValue(result_expr))
                    path_ok = [z3_v2 != 0]
                    
                    return [
                        (PC(pc.method, pc.offset + 1), state_ok, path_ok),
                        # Error state - special PC to indicate error
                    ]
                case jvm.BinaryOpr.Rem:
                    # Similar to division - check for zero
                    state_ok = new_state.copy()
                    result_expr = z3_v1 % z3_v2
                    state_ok.stack.push(SymValue(result_expr))
                    path_ok = [z3_v2 != 0]
                    return [(PC(pc.method, pc.offset + 1), state_ok, path_ok)]
                case _:
                    raise NotImplementedError(f"Binary operation {opr_type}")
            
            new_state.stack.push(SymValue(result_expr))
            return [(PC(pc.method, pc.offset + 1), new_state, path_constraint)]
        
        case jvm.Ifz(condition=cond, target=target):
            v = state.stack.pop()
            z3_v = to_z3_expr(v)
            
            # Create two branches: one where condition is true, one where false
            state_true = state.copy()
            state_false = state.copy()
            
            constraint_true = None
            constraint_false = None
            
            if cond == "eq":
                constraint_true = z3_v == 0
                constraint_false = z3_v != 0
            elif cond == "ne":
                constraint_true = z3_v != 0
                constraint_false = z3_v == 0
            elif cond == "lt":
                constraint_true = z3_v < 0
                constraint_false = z3_v >= 0
            elif cond == "le":
                constraint_true = z3_v <= 0
                constraint_false = z3_v > 0
            elif cond == "gt":
                constraint_true = z3_v > 0
                constraint_false = z3_v <= 0
            elif cond == "ge":
                constraint_true = z3_v >= 0
                constraint_false = z3_v < 0
            else:
                raise NotImplementedError(f"Ifz condition {cond}")
            
            # Return both branches
            return [
                (PC(pc.method, target), state_true, [constraint_true]),
                (PC(pc.method, pc.offset + 1), state_false, [constraint_false])
            ]
        
        case jvm.If(condition=cond, target=target):
            v2 = state.stack.pop()
            v1 = state.stack.pop()
            
            z3_v1 = to_z3_expr(v1)
            z3_v2 = to_z3_expr(v2)
            
            state_true = state.copy()
            state_false = state.copy()
            
            constraint_true = None
            constraint_false = None
            
            if cond == "eq":
                constraint_true = z3_v1 == z3_v2
                constraint_false = z3_v1 != z3_v2
            elif cond == "ne":
                constraint_true = z3_v1 != z3_v2
                constraint_false = z3_v1 == z3_v2
            elif cond == "lt":
                constraint_true = z3_v1 < z3_v2
                constraint_false = z3_v1 >= z3_v2
            elif cond == "le":
                constraint_true = z3_v1 <= z3_v2
                constraint_false = z3_v1 > z3_v2
            elif cond == "gt":
                constraint_true = z3_v1 > z3_v2
                constraint_false = z3_v1 <= z3_v2
            elif cond == "ge":
                constraint_true = z3_v1 >= z3_v2
                constraint_false = z3_v1 < z3_v2
            else:
                raise NotImplementedError(f"If condition {cond}")
            
            return [
                (PC(pc.method, target), state_true, [constraint_true]),
                (PC(pc.method, pc.offset + 1), state_false, [constraint_false])
            ]
        
        case jvm.Return(type=ret_type):
            # Terminal state - no next states
            return []
        
        case jvm.Dup():
            new_state = state.copy()
            v = new_state.stack.peek()
            new_state.stack.push(v)
            return [(PC(pc.method, pc.offset + 1), new_state, [])]

        case jvm.Store(type=jvm.Int(), index=i):
            new_state = state.copy()
            v = new_state.stack.pop()
            new_state.locals[i] = v
            return [(PC(pc.method, pc.offset + 1), new_state, [])]

        case jvm.Incr(index=i, amount=a):
            new_state = state.copy()

            sym_val = new_state.locals[i]
            z3_old = to_z3_expr(sym_val)

            # Compute new symbolic value
            z3_new = z3_old + a

            # Store new symbolic value back
            new_state.locals[i] = SymValue(z3_new)

            return [(PC(pc.method, pc.offset + 1), new_state, [])]

        case _:
            # For unimplemented operations, just advance PC
            logger.warning(f"Unimplemented symbolic operation: {opr}")
            return [(PC(pc.method, pc.offset + 1), state.copy(), [])]


def interesting(state: SymState, path: SymPath) -> str | None:
    """
    Check if the state represents an interesting condition to report.
    Returns a description if interesting, None otherwise.
    """
    # Example: Check if we can reach a state with specific properties
    # This is where you'd add your analysis logic
    
    # For now, just return None (no interesting states found)
    return None


def analyse(pc: PC, inputs: list[tuple[str, jvm.Type]], max_depth: int) -> list[str]:
    """
    Perform symbolic execution analysis up to max_depth.
    
    Args:
        pc: Starting program counter
        inputs: List of (name, type) pairs for input parameters
        max_depth: Maximum exploration depth
    
    Returns:
        Analysis result string
    """
    # Create symbolic variables for all inputs (assuming integers)
    var_names = [name for name, _ in inputs]
    symbolic_vars = z3.Ints(" ".join(var_names))
    
    # Handle single variable case
    if len(inputs) == 1:
        symbolic_vars = [symbolic_vars]
    
    # Create initial symbolic locals
    locals_dict = {i: var for i, var in enumerate(symbolic_vars)}
    state = SymState.from_locals(locals_dict)
    
    # Stack for depth-first search: (PC, SymState, SymPath, depth)
    stack: list[tuple[PC, SymState, SymPath, int]] = [(pc, state, [], 0)]

    visited = set()  # Track visited (pc, path_hash) to avoid infinite loops
    branches = []
    while stack:
        (current_pc, current_state, path, n) = stack.pop(-1)
        
        logger.debug(f"Exploring: {current_pc} at depth {n}")
        
        # Check if state is interesting
        issue = interesting(current_state, path)
        if issue:
            return f"found interesting state: {issue}"
        
        # Generate next states
        try:
            next_states = step(current_pc, current_state)
        except Exception as e:
            logger.warning(f"Error during step: {e}")
            continue
        
        for (next_pc, next_state, path_constraints) in next_states:
            # Add new path constraints
            new_path = path + path_constraints
            
            # Check if path is satisfiable
            solver = z3.Solver()
            solver.add(new_path)
            if new_path:
                check_if_branch_exists = lambda x, s: any(s in item for item in x)
                sat_status = "SAT" if solver.check() == z3.sat else "UNSAT"
                branch = f"Branch: {new_path}, Status: {sat_status}"
                if not check_if_branch_exists(branches, f"{new_path}"):
                    branches.append(branch)

            if solver.check() != z3.sat:
                logger.debug(f"Path unsatisfiable, skipping")
                continue
            
            # Check depth limit
            if n + 1 < max_depth:
                stack.append((next_pc, next_state, new_path, n + 1))
            else:
                logger.debug(f"Reached max depth at {next_pc}")

    return branches


# Run symbolic analysis
if __name__ == "__main__":
    methodid, input = jpamb.getcase()
    # Example: Analyze with symbolic inputs
    # You'll need to specify the input parameters based on your method signature
    inputs = [("x", jvm.Int()), ("y", jvm.Int())]  # Adjust based on actual inputs
    max_depth = 150
    
    analyse(PC(methodid, 0), inputs, max_depth)
