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
    if os.name == "nt":  # Windows
        site_packages = os.path.join(venv_path, "Lib", "site-packages")
    else:  # Unix/Linux/Mac
        # Find Python version directory
        lib_dir = os.path.join(venv_path, "lib")
        if os.path.exists(lib_dir):
            for item in os.listdir(lib_dir):
                if item.startswith("python"):
                    site_packages = os.path.join(
                        lib_dir, item, "site-packages"
                    )
                    if os.path.exists(site_packages):
                        return site_packages

    if os.path.exists(site_packages):
        return site_packages
    return None


def _find_method_in_module(module: types.ModuleType, method_name: str):
    """
    Search for a method within all classes in a module.

    Args:
        module: The imported module
        method_name: Name of the method to find

    Returns:
        Tuple of (class, method) if found, None otherwise
    """
    import inspect

    # Iterate through all members of the module
    for name, obj in inspect.getmembers(module):
        # Check if it's a class defined in this module
        if inspect.isclass(obj) and obj.__module__ == module.__name__:
            # Check if the class has the method
            if hasattr(obj, method_name):
                method = getattr(obj, method_name)
                if callable(method):
                    return obj, method

    return None


def _load_function_from_file(
    path: str, func_name: str, venv_path: Optional[str] = None, class_name: Optional[str] = None
) -> Callable:
    """
    Loads a function or class method from a Python file using a standard import mechanism
    that is compatible with coverage tools. Handles package detection for relative imports.

    Automatically detects whether the target is a module-level function or class method.
    If class_name is not provided, will search for the function at module level first,
    then search within all classes in the module.

    Args:
        path: Path to the Python file
        func_name: Name of the function or method to load
        venv_path: Optional path to virtual environment (for isolated dependencies)
        class_name: Optional class name (if loading a method). If None, auto-detects.

    Returns:
        Function object (for module-level functions), or tuple of (class, method) for class methods
    """
    path_obj = os.path.abspath(path)
    module_dir = os.path.dirname(path_obj)
    base_name = os.path.splitext(os.path.basename(path_obj))[0]

    # Detect package hierarchy by checking for __init__.py up the directory chain
    parts = [base_name]
    current_dir = module_dir
    while current_dir and current_dir != os.path.dirname(
        current_dir
    ):  # Stop at root
        init_path = os.path.join(current_dir, "__init__.py")
        if os.path.exists(init_path):
            parts.append(os.path.basename(current_dir))
            current_dir = os.path.dirname(current_dir)
        else:
            break

    # The package_root is now the directory just above the top-level package
    package_root = current_dir

    # Build the full module name
    if len(parts) > 1:
        mod_name = ".".join(reversed(parts))
    else:
        mod_name = parts[0]
        package_root = module_dir  # For non-package modules, root is the module's dir

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

    # Add the package root to the system path if not already present
    if package_root and package_root not in sys.path:
        sys.path.insert(0, package_root)
        added_paths.append(package_root)

    try:
        # Import the module
        module = importlib.import_module(mod_name)
        # It might have been imported before, so reload to get the latest version
        importlib.reload(module)
    finally:
        # Clean up sys.path in reverse order
        for path_to_remove in reversed(added_paths):
            if path_to_remove in sys.path:
                sys.path.remove(path_to_remove)

    # If class_name is explicitly provided, load from that class
    if class_name:
        cls = getattr(module, class_name, None)
        if cls is None:
            raise AttributeError(f"{path} has no class '{class_name}'")
        if not isinstance(cls, type):
            raise TypeError(f"'{class_name}' in {path} is not a class")

        method = getattr(cls, func_name, None)
        if method is None:
            raise AttributeError(f"Class '{class_name}' has no method '{func_name}'")
        if not callable(method):
            raise TypeError(f"'{func_name}' in class '{class_name}' is not callable")

        # Return both class and method
        return cls, method

    # Auto-detection: Try module-level function first
    func = getattr(module, func_name, None)

    # If found at module level and it's a plain function, return it
    if func is not None and isinstance(func, types.FunctionType):
        return func

    # Not found at module level or not a function, search in classes
    result = _find_method_in_module(module, func_name)
    if result:
        return result  # Returns (class, method) tuple

    # Not found anywhere
    if func is not None:
        # Found something but it's not a function or method
        raise TypeError(
            f"'{func_name}' in {path} exists but is not a function or method"
        )
    else:
        # Not found at all
        raise AttributeError(
            f"{path} has no function or method named '{func_name}'"
        )


class HarnessBuilder:
    def __init__(self, venv_path: Optional[str] = None):
        """
        Initialize harness builder.

        Args:
            venv_path: Optional path to virtual environment for isolated dependencies
        """
        self.venv_path = venv_path

    def build(self, target: TargetPair):
        """
        Build function/method references from target pair.

        For regular functions: Returns (func_a, func_b)
        For class methods: Returns ((cls_a, method_a), (cls_b, method_b))

        Args:
            target: TargetPair with file paths and function/class names

        Returns:
            Tuple of loaded functions/methods
        """
        result_a = _load_function_from_file(
            target.file_a, target.func_name, self.venv_path, target.class_name
        )
        result_b = _load_function_from_file(
            target.file_b, target.func_name, self.venv_path, target.class_name
        )

        # Update target metadata if we detected a class method
        if isinstance(result_a, tuple) and len(result_a) == 2:
            cls_a, method_a = result_a
            target.is_class_method = True
            if not target.class_name:  # Only set if not already set
                target.class_name = cls_a.__name__

        # For class methods, result is (cls, method) tuple
        # For functions, result is just the function
        return result_a, result_b
