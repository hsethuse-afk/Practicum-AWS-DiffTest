#!/usr/bin/env python3
"""
Simple dependency scanner - finds imports and creates requirements.txt
"""

import ast
import sys


def scan_file(filename):
    """Scan a Python file and extract import statements."""
    imports = set()

    with open(filename, 'r') as f:
        try:
            tree = ast.parse(f.read(), filename=filename)
        except SyntaxError as e:
            print(f"Error parsing {filename}: {e}")
            return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split('.')[0])

    return imports


def filter_stdlib(imports):
    """Remove standard library modules, keep only third-party."""
    # Common stdlib modules
    stdlib = {
        'abc', 'argparse', 'array', 'ast', 'asyncio', 'base64', 'bisect',
        'collections', 'copy', 'csv', 'dataclasses', 'datetime', 'decimal',
        'enum', 'functools', 'glob', 'hashlib', 'heapq', 'io', 'itertools',
        'json', 'logging', 'math', 'operator', 'os', 're', 'random', 'shutil',
        'socket', 'string', 'subprocess', 'sys', 'tempfile', 'threading',
        'time', 'typing', 'urllib', 'uuid', 'warnings', 'xml', 'pathlib'
    }

    return [pkg for pkg in imports if pkg not in stdlib]


def create_requirements(packages, output='requirements.txt'):
    """Create requirements.txt file."""
    # Package name mappings (import name -> package name)
    mappings = {
        'cv2': 'opencv-python',
        'PIL': 'Pillow',
        'sklearn': 'scikit-learn',
    }

    with open(output, 'w') as f:
        f.write("# Auto-generated requirements\n\n")
        for pkg in sorted(packages):
            # Map package name if needed
            package_name = mappings.get(pkg, pkg)
            f.write(f"{package_name}\n")

    print(f"✓ Created {output} with {len(packages)} packages")


def main():
    if len(sys.argv) < 3:
        print("Usage: python scan_dependencies.py <file_a> <file_b> [output]")
        sys.exit(1)

    file_a = sys.argv[1]
    file_b = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) > 3 else 'requirements.txt'

    print(f"Scanning dependencies...")
    print(f"  File A: {file_a}")
    print(f"  File B: {file_b}")

    # Scan both files
    imports_a = scan_file(file_a)
    imports_b = scan_file(file_b)

    # Combine
    all_imports = imports_a | imports_b

    print(f"\nFound imports: {sorted(all_imports)}")

    # Filter to third-party only
    third_party = filter_stdlib(all_imports)

    print(f"Third-party packages: {sorted(third_party)}")

    # Create requirements.txt
    create_requirements(third_party, output)

    print(f"\n✓ Done! Requirements saved to {output}")


if __name__ == '__main__':
    main()
