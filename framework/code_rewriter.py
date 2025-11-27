import shutil  # shell utilities
from pathlib import Path
from syntaxer import Map, Classes

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


def add_comments_to_file(class_file):
    class_file_path: Path = OUT / f"{class_file.class_name}.java"

    def add_assertion_prefix():
        """
        add_assertion_prefix adds the assertion per method to a new file, then appends the old file
        """
        avg = class_file.average_assertion_per_method
        if avg >= 2:
            prefix = f"// The file has on average {avg:.2f} assertions per method. This is sufficient.\n"
        else:
            prefix = f"// Warning! The file has on average {avg:.2f} assertions per method. This is not sufficient.\n"
        
        if class_file_path.exists():
            old_file = class_file_path.read_text()
            class_file_path.write_text(prefix + old_file)

    def add_comments():
        """
        add_comments will append a classification to each assertion line.
        """
        if not class_file_path.exists():
            return

        lines = class_file_path.read_text().splitlines(keepends=True)
        
        assertion_list = [
            a
            for m in class_file.methods
            for a in m.assertions
        ]
        
        assertion_list.sort(key=lambda x: x.absolute_start_point[0], reverse=True)
        
        for a in assertion_list:
            row = a.absolute_start_point[0] 
            
            if 0 <= row < len(lines):
                original_line = lines[row].rstrip('\n')
                comment = f" // {a.classification}"
                if comment not in original_line:
                    lines[row] = f"{original_line}{comment}\n"

        filestr: str = "".join(lines)
        class_file_path.write_text(filestr)
        
    add_comments()
    add_assertion_prefix()


def add_suggestions_file(class_file):
    """
    add_suggestions_file inserts suggested assertions into the method body 
    right after the opening brace '{'.
    """
    class_file_path: Path = OUT / f"{class_file.class_name}.java"
    
    if not class_file_path.exists():
        return

    lines = class_file_path.read_text().splitlines(keepends=True)

    methods_to_process = []
    for m in class_file.methods:
        raw_suggestions = m.get_suggested_assertions()
        valid_suggestions = []
        for s in raw_suggestions:
            clean_s = s.strip()
            valid_suggestions.append(clean_s)
        
        if valid_suggestions:
            methods_to_process.append((m, valid_suggestions))

    methods_to_process.sort(key=lambda x: x[0].method_node.start_point[0], reverse=True)

    for m, suggestions in methods_to_process:
        start_row = m.method_node.start_point[0]
        
        brace_index = -1
        for i in range(start_row, min(start_row + 20, len(lines))):
            line_stripped = lines[i].strip()
            
            if line_stripped.startswith("@"):
                continue
            
            if "{" in line_stripped:
                brace_index = i
                break
        
        if brace_index != -1:
            line_content = lines[brace_index]
            base_indent = line_content[:len(line_content) - len(line_content.lstrip())]
            new_indent = base_indent + "    "
            
            for s in reversed(suggestions):
                code = s
                lines.insert(brace_index + 1, f"{new_indent}{code} // suggested\n")

    class_file_path.write_text("".join(lines))


def rewrite_all_files(assertion_mapping):
    """
    rewrite_all_files iterates through the assertion mapping to comment each file.
    """
    copy_class_files()

    class_list: list = assertion_mapping.classes
    
    for cf in class_list:
        add_comments_to_file(cf)
        add_suggestions_file(cf)


def validate_mapping(assertion_mapping):
    """
    validate_mapping goes through the mapping and the annotated_OUTput_files, then it confirms that those classes are the exact same
    """
    assertion_classes = [cf.class_name for cf in assertion_mapping.classes]
    current_classes = [
        Path(class_file.name).stem for class_file in list(OUT.rglob("*.java"))]
    assert set(current_classes) == set(assertion_classes), f"mapping is not valid {current_classes} : {assertion_classes}"


def run(assertion_mapping: Map):
    copy_class_files()

    validate_mapping(assertion_mapping)
    rewrite_all_files(assertion_mapping)


if __name__ == "__main__":
    print(f"the file {__file__} is run\n")
