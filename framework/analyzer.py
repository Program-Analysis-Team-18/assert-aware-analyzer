import syntaxer
import classifier
import code_rewriter
import utils
import score
from fuzzer import Fuzzer
from score import calculate_performance

import time


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
                # fuzzer = f.Fuzzer(method.method_id)
                fuzzer.fuzz()

                for wrong_inputs_set in fuzzer.wrong_inputs:
                    method.add_wrong_inputs(wrong_inputs_set)

            except Exception as e:
                logger.error(f"Fuzzer failed for {method.method_name}: {e}")


def run(Syntatic_analysis_enabled=True, Assetion_solver_enabled=True, Dynamic_analysis_enabled=True, Symbolic_execution_enabled=True):
    logger = utils.configure_logger()
    start_syntatic_analysis = 0
    end_syntatic_analysis = 0

    # SYNTACTIC ANALYSIS
    if Syntatic_analysis_enabled:
        start_syntatic_analysis = time.time()
        assert_map = syntaxer.run()
        resolve_method_ids(assert_map, logger)
        end_syntatic_analysis = time.time()
    else:
        assert_map = syntaxer.return_empty_map()
        

    # ASSERT CLASSIFICATION
    # (Z3 Solver + Param Generation Fuzzer + Interpreter)
    if Assetion_solver_enabled or Dynamic_analysis_enabled:
        assert_map, time_measurements_classification_z3_dynamic = classifier.run(assert_map, Assetion_solver_enabled, Dynamic_analysis_enabled)
    else:
        time_measurements_classification_z3_dynamic = {'static_solver': 0, 'dynamic': 0}

    
    # COVERAGE BASED FUZZING
    start_time_fuzzing = time.time()
    run_fuzzing(assert_map, logger, symbolic_fuzzer=Symbolic_execution_enabled)
    end_time_fuzzing = time.time()

    time_measurements_fuzzing = end_time_fuzzing - start_time_fuzzing

    # CODE REWRITING
    # (Comments + Suggestions)
    start_time_rewriting = time.time()
    code_rewriter.run(assert_map)
    end_time_rewriting = time.time()

    time_measurements_rewriting = end_time_rewriting - start_time_rewriting

    print("Execution times:")
    print(f"Classification static: {end_syntatic_analysis-start_syntatic_analysis}")
    print(f"Classification z3_solver: {time_measurements_classification_z3_dynamic["static_solver"]}\nClassification dynamic: {time_measurements_classification_z3_dynamic["dynamic"]}")
    print(f"Classification static total: {time_measurements_classification_z3_dynamic['static_solver'] + (end_syntatic_analysis - start_syntatic_analysis)}")
    print(f"Classification total: {time_measurements_classification_z3_dynamic['static_solver'] + time_measurements_classification_z3_dynamic["dynamic"] + (end_syntatic_analysis - start_syntatic_analysis)}")
    print(f"Rewriting: {time_measurements_rewriting}")
    print(f"Fuzzing: {time_measurements_fuzzing} -------- Symbolic execution enabled: {Symbolic_execution_enabled}")

    calculate_performance(assert_map=assert_map)


if __name__ == "__main__":
    Syntatic_analysis_enabled = True
    Assetion_solver_enabled = True
    Dynamic_analysis_enabled = True

    Symbolic_execution_enabled = True
    run(Syntatic_analysis_enabled, Assetion_solver_enabled, Dynamic_analysis_enabled, Symbolic_execution_enabled)