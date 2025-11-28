import sys
from pathlib import Path
from loguru import logger


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

def configure_logger():
    """Configures the logger with a custom format."""
    logger.remove()
    logger.add(sys.stderr, format="[{level}] {message}")
    return logger

def get_dir_from_root(dir: str):
    if not dir.startswith("/"):
        dir = "/" + dir
    dir = dir.lstrip('/')
    return str(Path(__file__).resolve().parent.parent.joinpath(dir))
