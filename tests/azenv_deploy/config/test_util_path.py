import os
import sys

def __init_py_path__() -> None:
    """Initializes the python path. Allowing easy sharing of python code."""
    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    project_path= os.path.join(project_root, "projects")
    for py_path in [project_root,project_path]:
        if py_path not in sys.path:
            sys.path.append(py_path)

__init_py_path__()
