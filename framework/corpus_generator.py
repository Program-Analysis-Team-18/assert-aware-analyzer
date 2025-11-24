from z3 import *
import re

def parse_branches(lines):
    """
    Accepts a list of strings like:
      [
        'Branch: [a <= b], Status: SAT',
        'Branch: [a > b], Status: SAT',
        ...
      ]

    Returns: [([conditions], status), ...]
    """
    branches = []
    pattern = r"Branch:\s*\[(.*?)\],\s*Status:\s*(\w+)"

    for line in lines:
        match = re.search(pattern, line)
        if not match:
            continue
        conds_str, status = match.groups()

        cond_list = []
        if conds_str.strip():
            cond_list = [c.strip() for c in conds_str.split(",")]

        branches.append((cond_list, status))

    return branches


def extract_z3_variables(conditions):
    """
    Collect all symbolic variable names appearing in the conditions.
    Example: 'a > b' → {'a', 'b'}
    """
    vars_found = set()
    pattern = r"[a-zA-Z_]\w*"     # matches variable-like identifiers
    for cond in conditions:
        for v in re.findall(pattern, cond):
            # Exclude keywords/operators (but treat everything as var except ints)
            if not v.isdigit():
                vars_found.add(v)
    return sorted(vars_found)


def solve_branch(conds, method_params):
    """
    Solve the symbolic constraints with Z3.
    Returns a model mapping variable -> concrete value.
    """
    # Collect variables
    var_names = extract_z3_variables(conds)
    z3_vars = {name: Int(name) for name in var_names}

    s = Solver()
    for c in conds:
        s.add(eval(c, {}, z3_vars))

    if s.check() != sat:
        return None

    model = s.model()
    input = [model[z3_vars[name]].as_long() for name in var_names]
    if len(input) < len(method_params):
        input = input + [0 for _ in range(len(method_params))]
    return input


def generate_inputs(method_params, solution):
    """
    Format the solution into the same output structure
    your random_input() method generates:
      number of params = len(method_params)
      each param = the next integer from solution[]
    """
    if len(solution) < len(method_params):
        raise ValueError("Not enough symbolic values to fill all parameters.")

    return solution[:len(method_params)]


def generate_corpus(branches, method_params):
    branches_map = parse_branches(branches)
    corpus = []

    for conds, status in branches_map:
        if status == "SAT":
            sol = solve_branch(conds, method_params)
            if sol:
                corpus.append(generate_inputs(method_params, sol))
    return corpus
