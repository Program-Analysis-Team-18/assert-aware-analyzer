"""
Example on how to use this Solver Package.
`PYTHONPATH=. uv run framework/solver_example.py`
"""
import tree_sitter_java as tsjava
from tree_sitter import Language, Parser
from solver import AssertSolver
from solver import GenerationInvoker
from classifier import classify_base

JAVA_LANGUAGE = Language(tsjava.language())
parser = Parser(JAVA_LANGUAGE)

# code = """
# public class Test {
#     public static void withdraw(PositiveInteger balance, PositiveInteger amount) {
#         assert balance.get() != 0;                  // useful: avoid dividing by zero
#         assert balance.get() - amount.get() >= 0;   // useful: prevents overdrawing
#         assert balance.get() > 10;                  // useless: random, no safety gain
#         assert amount.get() + 10 > amount.get();    // tautology: always true
#         assert balance.get() - 10 > balance.get();  // contradiction: always false

#         int percentageWithdrawn = amount.get() * 100 / balance.get();
#         balance.set(balance.get() - amount.get());
#     }
# }
# """

code = """
public static void Withdraw(PositiveInteger amount) {
    PositiveInteger balance = new PositiveInteger(1c);
        
    assert balance.get() != 0;                  // useful: avoid dividing by zero
    assert balance.get() - amount.get() >= 0;   // useful: prevents overdrawing
    assert amount.get() > 10;                  // useless: random, no safety gain
    assert amount.get() + 10 > amount.get();    // tautology: always true
    assert balance.get() - 10 > balance.get();  // contradiction: always false
    int percentageWithdrawn = amount.get() * 100 / balance.get();
    balance.set(balance.get() - amount.get());

    return;
}
"""

tree = parser.parse(bytes(code, "utf8"))
root = tree.root_node
code_bytes = bytes(code, "utf8")

def extract_method_parameters(root, code: bytes, method_name: str):
    params = []

    def walk(node):
        if node.type == "method_declaration":
            name = node.child_by_field_name("name")
            if name and code[name.start_byte:name.end_byte].decode() == method_name:
                plist = node.child_by_field_name("parameters")
                if plist:
                    for p in plist.children:
                        if p.type == "formal_parameter":
                            vn = p.child_by_field_name("name")
                            vname = code[vn.start_byte:vn.end_byte].decode()
                            params.append(vname)
                return

        for c in node.children:
            walk(c)

    walk(root)
    return params


def find_asserts(node):
    """Find assert statements in the tree setter node tree."""
    if node.type == "assert_statement":
        return [node]
    res = []
    # TODO TODO
    # 1. check assertions indipendently
    # 2. then, keep track of the "useful" assertions
    # 3. then, execute useful assertions together based on the contained variables
    # 4a. then, suggest if groups of those assertions contains contradiction (no SAT)
    # 4b. also, suggest if groups of those assertions are self implied (useless) when combined together
    for c in node.children:
        res += find_asserts(c)
    return res

method_params_order = extract_method_parameters(root, code_bytes, "Withdraw")
# e.g. ["balance", "amount"]

print("method_params_order: ", method_params_order)

assert_nodes = find_asserts(root)

# uv run solutions/interpreter.py "jpamb.cases.CustomClasses.Withdraw:(Ljpamb/cases/PositiveInteger<init>I;)V" "(new jpamb/cases/PositiveInteger(1))"
method_id = "jpamb.cases.CustomClasses.Withdraw:(Ljpamb/cases/PositiveInteger<init>I;Ljpamb/cases/PositiveInteger<init>I;)V"

for a in assert_nodes:
    solver = AssertSolver([a])
    result = solver.solve()
    CLASSIFICATION = classify_base(result)

    if CLASSIFICATION == "contingent":
        # print("\n[+] Contingent assertion found")

        model = result.model                 # Z3 model
        z3_vars = result.variables           # dict[varname → z3var]

        inv = GenerationInvoker(method_id)
        

        # TODO add try catch
        try:
            # TODO MAKE THE FUZZER LOOK FOR INPUT THAT DOES NOT GENERATE ANY EXCEPTION (depth > 0)
            # you can also run multiple times
            
            output, formatted = inv.invoke(
                param_order=method_params_order,
                model=model,
                z3_vars=z3_vars
            )
        except Exception as e:
            print(f"EXCEPTION: {e!r}")
            print(f"{a.text.decode()} // USEFUL")
        else:
            # print("Generated input:", formatted)
            if output.message != "ok":
                print(f"MESSAGE: {output.message}")
                print(f"{a.text.decode()} // USEFUL")
            else:
                print(f"{a.text.decode()} // USELESS")
            # print("Execution output:", output.message)
    else:
        print(f"{a.text.decode()} // {CLASSIFICATION}")


# assert_nodes = find_asserts(root)

# for a in assert_nodes:
#     solver = AssertSolver([a], code_bytes)
#     result = solver.solve()
#     CLASSIFICATION = solver.classify_assertion(result)

#     # if CLASSIFICATION == "contingent":
#         # TODO
#         # invoke the generator invoker

#     print("Assertion:", a.text)
#     print("Status:", result.status)
#     print("Variables:", result.variables)
#     print("Model:", result.model)
#     print("Classification:", CLASSIFICATION)
#     print("")

# print("Status:", result["status"])
# print("Variables:", result["variables"])
# print("Model:", result["model"])
# print("Classification:", result["classification"])