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
    Solve symbolic constraints with Z3.
    """
    var_names = extract_z3_variables(conds)
    z3_vars = {}
    for name, t in zip(var_names, method_params):
        if t == 'I':
            z3_vars[name] = Int(name)
        elif t == 'C':
            z3_vars[name] = Int(name)
        elif t == 'Z':
            z3_vars[name] = Bool(name)
        else:
            raise ValueError(f"Unknown type '{t}'")

    s = Solver()
    for c in conds:
        s.add(eval(c, {}, z3_vars))

    if s.check() != sat:
        return None

    model = s.model()

    input_values = []
    for name, t in zip(var_names, method_params):
        val = model[z3_vars[name]]
        if t == 'I':
            input_values.append(val.as_long())
        elif t == 'C':
            input_values.append(chr(val.as_long()))
        elif t == 'Z':
            input_values.append(val == True)

    #pad missing values
    while len(input_values) < len(method_params):
        t = method_params[len(input_values)]
        if t == 'I':
            input_values.append(0)
        elif t == 'C':
            input_values.append('a')
        elif t == 'Z':
            input_values.append(False)

    return input_values


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


def generate_corpus(branches, primitive_params, method_params):
    branches_map = parse_branches(branches)
    corpus = []
    for conds, status in branches_map:
        if status == "SAT":
            sol = solve_branch(conds, primitive_params)
            if sol:
                corpus.append(generate_inputs(primitive_params, sol))

    unique_inputs = list(map(list, {tuple(x) for x in corpus}))
    param_count = 0
    while len(method_params) > 0:
        if method_params[0] == 'L':
            name = method_params[1:method_params.find('<init>')]
            ctor_params = method_params[method_params.find('<init>') + 6: method_params.find(';')]
            j = 0
            while j < len(unique_inputs):
                unique_inputs[j][param_count] = [name, unique_inputs[j][param_count]]
                j += 1
            method_params = method_params[method_params.find(';') + 1:]
            param_count += 1
        else:
            method_params = method_params[1:]
            param_count += 1
    return unique_inputs
