import importlib
import sys
import types
import os
from typing import Callable
from .contracts import TargetPair


def _load_function_from_file(path: str, func_name: str) -> Callable:
    """
    Loads a function from a Python file using a standard import mechanism
    that is compatible with coverage tools.
    """
    path_obj = os.path.abspath(path)
    dir_name = os.path.dirname(path_obj)
    mod_name = os.path.splitext(os.path.basename(path_obj))[0]

    # Temporarily add the file's directory to the system path
    if dir_name not in sys.path:
        sys.path.insert(0, dir_name)

    try:
        # Import the module
        module = importlib.import_module(mod_name)
        # It might have been imported before, so reload to get the latest version
        importlib.reload(module)
    finally:
        # Clean up sys.path
        if dir_name in sys.path and sys.path[0] == dir_name:
            sys.path.pop(0)

    func = getattr(module, func_name, None)
    if not callable(func):
        raise AttributeError(f"{path} has no callable '{func_name}'")
    # Ensure it's a plain function (early-stage guard)
    if not isinstance(func, types.FunctionType):
        raise TypeError(
            f"'{func_name}' in {path} is not a plain function"
        )
    return func


class HarnessBuilder:
    def build(self, target: TargetPair) -> tuple[Callable, Callable]:
        f_a = _load_function_from_file(target.file_a, target.func_name)
        f_b = _load_function_from_file(target.file_b, target.func_name)
        return f_a, f_b
