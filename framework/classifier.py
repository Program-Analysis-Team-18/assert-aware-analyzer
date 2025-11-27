import z3

from core import Map, Classification
from solver import AssertSolver, GenerationInvoker, SolveResult


def classify_base(result: SolveResult) -> Classification:
    """
    Classify assertions based on the z3 solver result (status + model).
    Possible classifications are:
    - 'tautology'
    - 'contingent'
    - 'contradiction'
    - 'unclassified'
    """
    match result.status:
        case z3.unsat:
            classification = "tautology"
        case z3.sat:
            if result.model:
                classification = "contingent"
            else:
                classification = "contradiction"
        case _:
            classification = "unclassified"

    return classification

def classify_advanced(result: SolveResult, method_id: str, params_order: list[str], max_attempts: int = 10) -> Classification:
    """
    Uses the interpreter to classify the assertion as useful or useless.
    The assertion is useful if running with a possible solution throws an exception.
    The assertion is useless otherwise.
    """
    # 0. only "contingent" must be checked
    # 1. convert parameters to input values
    # 2. if any missing parameter, generate random values
    # 3. otherwise, provide default values for all out test
    # 4. if the execution throws an exception, classify the assert as useful
    assert result.status == z3.sat and result.model, f"Not a 'contingent' assertion {method_id}"
    model = result.model
    z3_vars = result.variables

    invoker = GenerationInvoker(method_id)

    try:
        output = invoker.invoke(params_order, model, z3_vars)
    except Exception as e:
        # print(f"EXCEPTION {e}")
        return 'useful', output.depth
    else:
        if output.message != "ok":
            # print(f"MESSAGE {output.message}")
            return 'useful', output.depth
        else:
            return 'useless', output.depth


def run(assert_map: Map) -> Map:
    """Classify all assertions not classified from Syntactic Analysis."""
    for c in assert_map.classes:
        # print(f"====== CLASS: {c.class_name} ======")
        for m in c.methods:
            # print(f"\n====== METHOD: {m.method_name} ======")
            for a in m.assertions:
                # print(f"\n====== ASSERT: {a.assertion_node.text.decode()} ======")

                classification = a.classification
                if classification == 'unclassified':
                    # base classification
                    solver = AssertSolver([a.assertion_node])
                    result = solver.solve()
                    classification = classify_base(result)

                    # advanced classification
                    if classification == 'contingent':
                        # find method id from methods.txt using method name
                        # TODO: extract logic in analyzer
                        params_order = [p.name for p in m.parameters]

                        for i in range(2,10):
                            classification, depth = classify_advanced(result, m.method_id, params_order)
                            if classification != 'useful' or depth != 0:
                                break
                            solver = AssertSolver([a.assertion_node])
                            result = solver.solve(attempts=i)
                            
                a.classification = classification

    return assert_map