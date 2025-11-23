import shutil  # shell utilities
from pathlib import Path
import static_analysis
import code_rewriter





if __name__ == "__main__":
    print(f"the file {__file__} is run\n")
    assert_map = static_analysis.run()
    code_rewriter.run(assert_map)

