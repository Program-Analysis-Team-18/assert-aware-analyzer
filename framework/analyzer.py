import syntaxer
import classifier
import code_rewriter
import utils
from fuzzer import Fuzzer


def resolve_method_ids(assert_map, logger):
    """
    Assign fully-qualified method IDs to each method using utils.find_fully_qualified_method.
    Methods whose IDs cannot be resolved are skipped.
    """
    for cls in assert_map.classes:
        for method in cls.methods:
            try:
                method_id = utils.find_fully_qualified_method(method.method_name)
                method.set_method_id(method_id)
            except Exception as e:
                logger.warning(f"Could not resolve method id for {method.method_name}: {e}")


def run_fuzzing(assert_map, logger, symbolic_fuzzer=False):
    """
    Run fuzzing for every method that has parameters.
    Collect wrong inputs from the fuzzer and attach them to the Method object.
    """
    for cls in assert_map.classes:
        for method in cls.methods:
            if not method.parameters:
                continue

            if not hasattr(method, "method_id"):
                logger.warning(f"Method {method.method_name} has no method_id. Skipping fuzzer.")
                continue

            try:
                fuzzer = Fuzzer(method.method_id, symbolic_corpus=symbolic_fuzzer)
                fuzzer.fuzz()

                for wrong_inputs_set in fuzzer.wrong_inputs:
                    method.add_wrong_inputs(wrong_inputs_set)

            except Exception as e:
                logger.error(f"Fuzzer failed for {method.method_name}: {e}")


def run():
    logger = utils.configure_logger()

    # SYNTACTIC ANALYSIS
    assert_map = syntaxer.run()

    resolve_method_ids(assert_map, logger)

    # ASSERT CLASSIFICATION
    # (Z3 Solver + Param Generation Fuzzer + Interpreter)
    assert_map = classifier.run(assert_map)

    # COVERAGE BASED FUZZING
    symbolic_exec_enable = True

    run_fuzzing(assert_map, logger, symbolic_fuzzer=symbolic_exec_enable)

    # CODE REWRITING
    # (Comments + Suggestions)
    code_rewriter.run(assert_map)


if __name__ == "__main__":
    run()