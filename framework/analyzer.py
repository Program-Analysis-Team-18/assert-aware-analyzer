from framework import syntaxer
from framework import classifier

assert_map = syntaxer.run()
assert_map = classifier.run(assert_map)
# wrong_inputs = fuzzer
# code_rewriter.run(assert_map, wrong_inputs)

# TODO: replace with Code Rewriter logic
for c in assert_map.classes:
    for m in c.methods:
        if len(m.assertions) > 0:
            print(f"\n=== CLASS: {c.class_name}, METHOD: {m.method_name} ===")
        for a in m.assertions:
            print(f"{a.assertion_node.text.decode()} // {a.classification}")
