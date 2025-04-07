"""
Initializes the PyPath to enable code sharing for Pulumi.
This will add the project code root directory to `PYTHONPATH`, so the classes define
in the code directory can be used in project directory here.

See: 
https://stackoverflow.com/questions/16981921/relative-imports-in-python-3#:~:text=that%20directory%20to-,PYTHONPATH,-(either%20one%20will
https://docs.python.org/3/library/sys_path_init.html
"""
# pylint: disable=duplicate-code
import os
import sys


def pylint_ignore_module() -> None:
    """Dummy method to avoid pylint warnings"""


def __init_py_path__() -> None:
    """Initializes the python path. Allowing easy sharing of python code across Pulumi projects."""
    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    project_code_root = os.path.join(project_root, "azenv_deploy/azenv_deploy")

    for py_path in [project_root, project_code_root]:
        if py_path not in sys.path:
            sys.path.append(py_path)

__init_py_path__()
