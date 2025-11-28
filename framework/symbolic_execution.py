from pathlib import Path

import jpamb
from jpamb import jvm
from dataclasses import dataclass
import z3
from typing import Iterable

import sys
from loguru import logger

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


suite = jpamb.Suite(Path(__file__).parent.joinpath("../"))
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
        
        case jvm.Load(type=jvm.Reference(), index=i):
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
                    # Path 1: successful division
                    state_ok = new_state.copy()
                    result_expr = z3_v1 / z3_v2
                    state_ok.stack.push(SymValue(result_expr))
                    path_ok = [z3_v2 != 0]
                    
                    return [(PC(pc.method, pc.offset + 1), state_ok, path_ok)]
                case jvm.BinaryOpr.Rem:
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
        
        case jvm.Dup(words=1):
            new_state = state.copy()
            v = new_state.stack.peek()
            new_state.stack.push(v)
            return [(PC(pc.method, pc.offset + 1), new_state, [])]

        case jvm.Store(type=_, index=i):
            new_state = state.copy()
            v = new_state.stack.pop()
            new_state.locals[i] = v
            return [(PC(pc.method, pc.offset + 1), new_state, [])]

        case jvm.Incr(index=i, amount=a):
            new_state = state.copy()
            sym_val = new_state.locals[i]
            z3_old = to_z3_expr(sym_val)
            z3_new = z3_old + a
            new_state.locals[i] = SymValue(z3_new)
            return [(PC(pc.method, pc.offset + 1), new_state, [])]

        case jvm.Goto(target=t):
            new_state = state.copy()
            return [(PC(pc.method, t), new_state, [])]

        case jvm.Get(static=True, field=f):
            # For symbolic execution, we can treat static fields as symbolic values
            new_state = state.copy()
            # Create a symbolic variable for this static field
            clean_name = f.fieldid.name.replace("$", "")
            field_var = z3.Int(f"field_{clean_name}")
            new_state.stack.push(SymValue(field_var))
            return [(PC(pc.method, pc.offset + 1), new_state, [])]

        case jvm.Get(static=False, field=f):
            # Get instance field
            new_state = state.copy()
            objref = new_state.stack.pop()
            
            # In symbolic execution, we need to handle this symbolically
            # For now, create a symbolic variable representing the field value
            field_var = z3.Int(f"field_{f.fieldid.name}")
            new_state.stack.push(SymValue(field_var))
            return [(PC(pc.method, pc.offset + 1), new_state, [])]

        case jvm.Put(static=False, field=f):
            # Put instance field
            new_state = state.copy()
            value = new_state.stack.pop()
            objref = new_state.stack.pop()
            # In symbolic execution, we track this as a heap update
            # For simplicity, just continue without modeling heap deeply
            return [(PC(pc.method, pc.offset + 1), new_state, [])]

        case jvm.NewArray(type=t, dim=1):
            # Create new array - in symbolic execution, create symbolic reference
            new_state = state.copy()
            size = new_state.stack.pop()
            # Create a symbolic reference to the array
            array_ref = z3.Int(f"array_ref_{pc.offset}")
            new_state.stack.push(SymValue(array_ref))
            return [(PC(pc.method, pc.offset + 1), new_state, [])]

        case jvm.NewArray(type=t, dim=2):
            # Create 2D array
            new_state = state.copy()
            d2 = new_state.stack.pop()
            d1 = new_state.stack.pop()
            # Create symbolic reference
            array_ref = z3.Int(f"matrix_ref_{pc.offset}")
            new_state.stack.push(SymValue(array_ref))
            return [(PC(pc.method, pc.offset + 1), new_state, [])]

        case jvm.ArrayStore(type=t):
            # Store value into array
            new_state = state.copy()
            value = new_state.stack.pop()
            index = new_state.stack.pop()
            arrayref = new_state.stack.pop()
            # In symbolic execution, we would model this as a heap update
            # For now, just continue
            return [(PC(pc.method, pc.offset + 1), new_state, [])]

        case jvm.ArrayLoad(type=t):
            # Load value from array
            new_state = state.copy()
            index = new_state.stack.pop()
            arrayref = new_state.stack.pop()
            # Create symbolic value for array element
            elem_var = z3.Int(f"array_elem_{pc.offset}")
            new_state.stack.push(SymValue(elem_var))
            return [(PC(pc.method, pc.offset + 1), new_state, [])]

        case jvm.ArrayLength():
            # Get array length
            new_state = state.copy()
            arrayref = new_state.stack.pop()
            # Create symbolic length
            length_var = z3.Int(f"array_length_{pc.offset}")
            new_state.stack.push(SymValue(length_var))
            return [(PC(pc.method, pc.offset + 1), new_state, [])]

        case jvm.New(classname=cn):
            # Create new object
            new_state = state.copy()
            # Create symbolic reference to the object
            obj_ref = z3.Int(f"obj_ref_{cn.name}_{pc.offset}")
            new_state.stack.push(SymValue(obj_ref))
            return [(PC(pc.method, pc.offset + 1), new_state, [])]

        case jvm.InvokeStatic(method=m) | jvm.InvokeVirtual(method=m) | jvm.InvokeSpecial(method=m, is_interface=_):
            # For symbolic execution, we can either:
            # 1. Inline the method call (recursive symbolic execution)
            # 2. Create symbolic return value (approximation)
            # For now, use option 2 for simplicity
            new_state = state.copy()
            
            # Pop arguments
            num_args = len(m.methodid.params)
            if not isinstance(opr, jvm.InvokeStatic):
                num_args += 1  # Include 'this' reference
            
            for _ in range(num_args):
                new_state.stack.pop()
            
            # If method has return type, push symbolic return value
            # if m.methodid.returntype is not None and m.methodid.returntype != jvm.Void():
            #     ret_var = z3.Int(f"ret_{m.methodid.name}_{pc.offset}")
            #     new_state.stack.push(SymValue(ret_var))
            
            return [(PC(pc.method, pc.offset + 1), new_state, [])]

        case jvm.Cast(from_=f, to_=t):
            # Type cast - in symbolic execution, preserve the symbolic value
            new_state = state.copy()
            value = new_state.stack.pop()
            new_state.stack.push(value)  # Keep same symbolic value
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
            raise ValueError(f"Symbolic Interpreter error: {e} in {bc[current_pc]}")
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

    # print(f"BRANCHES \n{branches}")
    return branches

if __name__ == "__main__":
    methodid, input = jpamb.getcase()
    inputs = [("x", jvm.Int())]  # Adjust based on actual inputs
    max_depth = 150

    print(analyse(PC(methodid, 0), inputs, max_depth))
