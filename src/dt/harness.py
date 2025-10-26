import importlib
import sys
import types
import os
import site
from typing import Callable, Optional
from .contracts import TargetPair


def _get_venv_site_packages(venv_path: str) -> Optional[str]:
    """Get the site-packages directory of a virtual environment"""
    if not venv_path:
        return None

    # Try to find site-packages in the venv
    if os.name == 'nt':  # Windows
        site_packages = os.path.join(venv_path, "Lib", "site-packages")
    else:  # Unix/Linux/Mac
        # Find Python version directory
        lib_dir = os.path.join(venv_path, "lib")
        if os.path.exists(lib_dir):
            for item in os.listdir(lib_dir):
                if item.startswith("python"):
                    site_packages = os.path.join(lib_dir, item, "site-packages")
                    if os.path.exists(site_packages):
                        return site_packages

    if os.path.exists(site_packages):
        return site_packages
    return None


def _load_function_from_file(path: str, func_name: str, venv_path: Optional[str] = None) -> Callable:
    """
    Loads a function from a Python file using a standard import mechanism
    that is compatible with coverage tools.

    Args:
        path: Path to the Python file
        func_name: Name of the function to load
        venv_path: Optional path to virtual environment (for isolated dependencies)
    """
    path_obj = os.path.abspath(path)
    dir_name = os.path.dirname(path_obj)
    mod_name = os.path.splitext(os.path.basename(path_obj))[0]

    # Track what we added to sys.path so we can clean it up
    added_paths = []

    # Add virtual environment's site-packages if provided
    if venv_path:
        site_packages = _get_venv_site_packages(venv_path)
        if site_packages and site_packages not in sys.path:
            sys.path.insert(0, site_packages)
            added_paths.append(site_packages)

    # Add current working directory to support project module imports
    cwd = os.getcwd()
    if cwd not in sys.path:
        sys.path.insert(0, cwd)
        added_paths.append(cwd)

    # Add the file's directory to the system path
    if dir_name not in sys.path:
        sys.path.insert(0, dir_name)
        added_paths.append(dir_name)

    try:
        # Import the module
        module = importlib.import_module(mod_name)
        # It might have been imported before, so reload to get the latest version
        importlib.reload(module)
    finally:
        # Clean up sys.path in reverse order
        for path_to_remove in added_paths:
            if path_to_remove in sys.path:
                sys.path.remove(path_to_remove)

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
    def __init__(self, venv_path: Optional[str] = None):
        """
        Initialize harness builder.

        Args:
            venv_path: Optional path to virtual environment for isolated dependencies
        """
        self.venv_path = venv_path

    def build(self, target: TargetPair) -> tuple[Callable, Callable]:
        f_a = _load_function_from_file(target.file_a, target.func_name, self.venv_path)
        f_b = _load_function_from_file(target.file_b, target.func_name, self.venv_path)
        return f_a, f_b
