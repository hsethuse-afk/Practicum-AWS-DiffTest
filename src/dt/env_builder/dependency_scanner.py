"""
Dependency scanner that analyzes Python files to detect required packages.
"""

import ast
import os
import re
from pathlib import Path
from typing import Set, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class DependencyInfo:
    """Information about discovered dependencies."""

    imports: Set[str] = field(default_factory=set)
    """Direct imports found in the code."""

    stdlib_modules: Set[str] = field(default_factory=set)
    """Standard library modules."""

    third_party_packages: Set[str] = field(default_factory=set)
    """Third-party packages that need to be installed."""

    local_imports: Set[str] = field(default_factory=set)
    """Local module imports within the project."""

    requirements_files: List[Path] = field(default_factory=list)
    """Found requirements.txt files."""

    def merge(self, other: 'DependencyInfo') -> None:
        """Merge another DependencyInfo into this one."""
        self.imports.update(other.imports)
        self.stdlib_modules.update(other.stdlib_modules)
        self.third_party_packages.update(other.third_party_packages)
        self.local_imports.update(other.local_imports)
        self.requirements_files.extend(other.requirements_files)


class DependencyScanner:
    """
    Scans Python files to discover dependencies.

    This scanner identifies:
    - Standard library imports
    - Third-party package imports
    - Local module imports
    - Requirements files
    """

    # Common standard library modules (Python 3.11)
    STDLIB_MODULES = {
        'abc', 'argparse', 'array', 'ast', 'asyncio', 'atexit', 'base64',
        'bisect', 'builtins', 'calendar', 'collections', 'contextlib', 'copy',
        'csv', 'dataclasses', 'datetime', 'decimal', 'difflib', 'enum', 'errno',
        'functools', 'gc', 'glob', 'hashlib', 'heapq', 'html', 'http', 'importlib',
        'inspect', 'io', 'itertools', 'json', 'logging', 'math', 'multiprocessing',
        'numbers', 'operator', 'os', 'pathlib', 'pickle', 'platform', 'pprint',
        'queue', 'random', 're', 'secrets', 'shutil', 'signal', 'socket', 'sqlite3',
        'statistics', 'string', 'struct', 'subprocess', 'sys', 'tempfile', 'textwrap',
        'threading', 'time', 'traceback', 'types', 'typing', 'unittest', 'urllib',
        'uuid', 'warnings', 'weakref', 'xml', 'zipfile', 'zoneinfo',
    }

    # Known package name mappings (import name -> package name)
    PACKAGE_MAPPINGS = {
        'cv2': 'opencv-python',
        'PIL': 'Pillow',
        'sklearn': 'scikit-learn',
        'yaml': 'pyyaml',
        'bs4': 'beautifulsoup4',
        'dateutil': 'python-dateutil',
    }

    def __init__(self):
        self.logger = None

    def scan_file(self, file_path: str) -> DependencyInfo:
        """
        Scan a single Python file for dependencies.

        Args:
            file_path: Path to the Python file

        Returns:
            DependencyInfo object with discovered dependencies
        """
        deps = DependencyInfo()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse the AST
            tree = ast.parse(content, filename=file_path)

            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name.split('.')[0]
                        deps.imports.add(module_name)
                        self._categorize_import(module_name, deps)

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module.split('.')[0]
                        deps.imports.add(module_name)
                        self._categorize_import(module_name, deps)

        except Exception as e:
            if self.logger:
                self.logger.debug(f"Error scanning {file_path}: {e}")

        return deps

    def scan_directory(self, directory: str, recursive: bool = True) -> DependencyInfo:
        """
        Scan a directory for Python files and extract dependencies.

        Args:
            directory: Path to the directory
            recursive: Whether to scan subdirectories

        Returns:
            Aggregated DependencyInfo for all files
        """
        deps = DependencyInfo()
        dir_path = Path(directory)

        # Find requirements.txt files
        req_files = list(dir_path.glob('requirements*.txt'))
        deps.requirements_files.extend(req_files)

        # Find all Python files
        pattern = '**/*.py' if recursive else '*.py'
        py_files = dir_path.glob(pattern)

        for py_file in py_files:
            if '__pycache__' in str(py_file):
                continue

            file_deps = self.scan_file(str(py_file))
            deps.merge(file_deps)

        return deps

    def scan_files(self, file_paths: List[str]) -> DependencyInfo:
        """
        Scan multiple specific files for dependencies.

        Args:
            file_paths: List of file paths to scan

        Returns:
            Aggregated DependencyInfo
        """
        deps = DependencyInfo()

        for file_path in file_paths:
            if os.path.isfile(file_path):
                file_deps = self.scan_file(file_path)
                deps.merge(file_deps)
            elif os.path.isdir(file_path):
                # Get the directory containing the file
                dir_deps = self.scan_directory(file_path, recursive=False)
                deps.merge(dir_deps)

        return deps

    def scan_project(self, project_root: str,
                     file_a: Optional[str] = None,
                     file_b: Optional[str] = None) -> DependencyInfo:
        """
        Scan an entire project including specific files A and B.

        Args:
            project_root: Root directory of the project
            file_a: Optional path to version A file
            file_b: Optional path to version B file

        Returns:
            Complete dependency information for the project
        """
        deps = DependencyInfo()

        # Scan project root
        project_deps = self.scan_directory(project_root, recursive=True)
        deps.merge(project_deps)

        # Scan specific files if provided
        if file_a and os.path.exists(file_a):
            deps_a = self.scan_file(file_a)
            deps.merge(deps_a)

        if file_b and os.path.exists(file_b):
            deps_b = self.scan_file(file_b)
            deps.merge(deps_b)

        return deps

    def extract_requirements_from_files(self, deps: DependencyInfo) -> Set[str]:
        """
        Extract package requirements from requirements.txt files.

        Args:
            deps: DependencyInfo containing requirements files

        Returns:
            Set of package requirements
        """
        requirements = set()

        for req_file in deps.requirements_files:
            try:
                with open(req_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        # Skip comments and empty lines
                        if not line or line.startswith('#'):
                            continue
                        # Extract package name (before version specifier)
                        match = re.match(r'^([a-zA-Z0-9\-_\.]+)', line)
                        if match:
                            requirements.add(match.group(1))
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"Error reading {req_file}: {e}")

        return requirements

    def get_install_requirements(self, deps: DependencyInfo) -> List[str]:
        """
        Get the list of packages that need to be installed.

        Args:
            deps: DependencyInfo object

        Returns:
            List of package names to install
        """
        # Start with third-party packages
        packages = set(deps.third_party_packages)

        # Add packages from requirements files
        req_packages = self.extract_requirements_from_files(deps)
        packages.update(req_packages)

        return sorted(list(packages))

    def _categorize_import(self, module_name: str, deps: DependencyInfo) -> None:
        """
        Categorize an import as stdlib, third-party, or local.

        Args:
            module_name: Name of the imported module
            deps: DependencyInfo to update
        """
        # Check if it's a standard library module
        if module_name in self.STDLIB_MODULES:
            deps.stdlib_modules.add(module_name)
            return

        # Check if it's a relative import or local module
        # (heuristic: single letter or starts with underscore might be local)
        if len(module_name) == 1 or module_name.startswith('_'):
            deps.local_imports.add(module_name)
            return

        # Map package name if needed
        package_name = self.PACKAGE_MAPPINGS.get(module_name, module_name)

        # Assume it's a third-party package
        deps.third_party_packages.add(package_name)

    def generate_requirements_txt(self, deps: DependencyInfo,
                                   output_path: str = "requirements_generated.txt") -> None:
        """
        Generate a requirements.txt file from discovered dependencies.

        Args:
            deps: DependencyInfo object
            output_path: Path where to write the requirements file
        """
        packages = self.get_install_requirements(deps)

        with open(output_path, 'w') as f:
            f.write("# Auto-generated requirements from dependency scanner\n")
            f.write("# Generated for differential testing environment\n\n")
            for package in packages:
                f.write(f"{package}\n")
