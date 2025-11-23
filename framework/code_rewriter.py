import shutil  # shell utilities
from pathlib import Path
import static_analysis

def copy_class_files():
    """
    copy_class_files makes copies of the .java class files
    """
    BASE = Path(__file__).resolve().parent.parent
    root = Path("src/main/java/jpamb/cases")
    out = Path(str(BASE / "annotated_output_files"))
    out.mkdir(parents=True, exist_ok=True)

    for class_file in list(root.rglob("*.java")):
        shutil.copyfile(str(class_file), str(out / class_file.name))

def add_comments_to_file(class_file: Path):
    print(f"class_file.resolve(): {class_file.resolve()}")

    # with open(class_file, "a") as f:
    #     f.write("Hello")
def comment_all_files():
    root = Path("src/main/java/jpamb/cases")

    for class_file in list(root.rglob("*.java"))[:1]:
        add_comments_to_file(class_file)



if __name__ == "__main__":
    copy_class_files()
    comment_all_files()


