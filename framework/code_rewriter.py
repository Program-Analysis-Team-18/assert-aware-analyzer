import shutil  # shell utilities
from pathlib import Path
from static_analysis import Map, Classes

# Declaring global path elements. This way does not matter from which directory you run the file
BASE = Path(__file__).resolve().parent.parent
ROOT = Path(BASE / "src/main/java/jpamb/cases")
OUT = Path(str(BASE / "annotated_output_files"))

def copy_class_files():
    """
    copy_class_files makes copies of the .java class files
    """
    OUT.mkdir(parents=True, exist_ok=True)

    for class_file in list(ROOT.rglob("*.java")):
        shutil.copyfile(str(class_file), str(OUT / class_file.name))

def add_comments_to_file(class_file: Classes):
    class_file_path: Path = OUT / f"{class_file.class_name}.java"
    print(f"class_file_path: {class_file_path}")

    def add_assertion_prefix():
        """
        add_assertion_prefix adds the assesrtion per method to a new file, then appends the old file
        """
        avg = class_file.average_assertion_per_method
        if avg >= 2:
            prefix = f"// The file has on average {avg} assertions per method. This is sufficient"
        else:  prefix = f"// The file has on average {avg} assertions per method. This is not sufficient\n"
        old_file = class_file_path.read_text()
        class_file_path.write_text(prefix + old_file)
    add_assertion_prefix()

def comment_all_files(assertion_mapping):
    class_list: list[Classes] = assertion_mapping.classes
    for cf in class_list:
        add_comments_to_file(cf)
    


def validate_mapping(assertion_mapping):
    """
    validate_mapping goes through the mapping and the annotated_OUTput_files, then it confirms that those classes are the exact same
    """
    assertion_classes = [cf.class_name for cf in assertion_mapping.classes]
    current_classes = [Path(class_file.name).stem for class_file in list(ROOT.rglob("*.java"))]
    assert set(current_classes) == set(assertion_classes), "mapping is not valid"




def run(assertion_mapping: Map):
    copy_class_files()

    validate_mapping(assertion_mapping)
    comment_all_files(assertion_mapping)


if __name__ == "__main__":
    print(f"the file {__file__} is run\n")


