from pathlib import Path

import syntaxer
import classifier
import code_rewriter
from fuzzer import Fuzzer


def find_fully_qualified_method(method_name: str) -> str:
    """
    Lookup the fully-qualified method id in `framework/methods.txt` by method name.
    Returns the first matching fully-qualified string.
    """
    methods_file = Path(__file__).parent.joinpath("methods.txt")
    if not methods_file.exists():
        raise FileNotFoundError(f"methods file not found: {methods_file}")

    with methods_file.open() as f:
        for line in f:
            s = line.strip()
            if method_name in s:
                return s
    raise ValueError(f"No method found for name {method_name!r} in {methods_file}")


if __name__ == "__main__":
    assert_map = syntaxer.run()

    for c in assert_map.classes:
        for m in c.methods:
            if len(m.assertions) > 0:
                try:
                    method_id = find_fully_qualified_method(m.method_name)
                    m.set_method_id(method_id)
                except Exception as e:
                    print(f"Could not resolve method id for {m.method_name}: {e}")
                    continue

    assert_map = classifier.run(assert_map)

    for c in assert_map.classes:
        for m in c.methods:
            print("ANALYSING METHOD: ", m.method_name)
            if len(m.assertions) > 0:
                fuzzer = Fuzzer(m.method_id)
                fuzzer.fuzz()
                m.add_wrong_args(fuzzer.wrong_args)
                
    # TODO add the code rewriter should suggest assertions only with faulty = True
    code_rewriter.run(assert_map)
