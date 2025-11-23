import shutil  # shell utilities
from pathlib import Path
import static_analysis
import code_rewriter





if __name__ == "__main__":
    assert_map = static_analysis.run()
    # code_rewriter.run(assert_map, wrong_inputs)
    print("test")
    print("test")
    assert_map.print_mapping

