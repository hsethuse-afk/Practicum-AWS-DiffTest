"""
Simple environment setup - scans code, creates requirements, builds Docker environment.
"""

import ast
import os
import subprocess
from pathlib import Path


def scan_imports(file_path):
    """Scan a Python file for import statements."""
    imports = set()

    with open(file_path, 'r') as f:
        tree = ast.parse(f.read())

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split('.')[0])

    return imports


def get_third_party_packages(imports):
    """Filter out stdlib, keep only third-party packages."""
    stdlib = {
        'os', 'sys', 'ast', 'json', 're', 'math', 'random', 'datetime',
        'collections', 'itertools', 'functools', 'pathlib', 'typing',
        'dataclasses', 'enum', 'subprocess', 'io', 'time', 'copy'
    }

    return sorted([pkg for pkg in imports if pkg not in stdlib])


def scan_codebase(file_a, file_b):
    """Scan both files and codebase for dependencies."""
    all_imports = set()

    # Scan file A and B
    for file_path in [file_a, file_b]:
        if os.path.exists(file_path):
            imports = scan_imports(file_path)
            all_imports.update(imports)

    # Get third-party packages
    packages = get_third_party_packages(all_imports)

    return packages


def create_requirements(packages):
    """Create requirements.txt with discovered packages."""
    # Base requirements for the framework
    base_reqs = [
        'hypothesis>=6.0.0',
        'coverage>=7.0.0',
        'libcst>=1.0.0',
        'righttyper>=0.1.0',
    ]

    # Combine with discovered packages
    all_reqs = base_reqs + packages

    # Save in project root
    project_root = Path(__file__).parent.parent.parent.parent
    output_file = project_root / "requirements_env.txt"

    with open(output_file, 'w') as f:
        f.write("# Auto-generated requirements for differential testing\n\n")
        for req in all_reqs:
            f.write(f"{req}\n")

    print(f"✓ Created {output_file} with {len(all_reqs)} packages")
    return str(output_file)


def build_docker_env(requirements_file):
    """Build Docker environment with requirements."""
    print("Building Docker environment...")

    # Find project root (where Dockerfile is)
    project_root = Path(__file__).parent.parent.parent.parent

    result = subprocess.run(
        ["docker", "build", "-t", "difftest-env", str(project_root)],
        capture_output=True,
        text=True,
        cwd=str(project_root)
    )

    if result.returncode == 0:
        print("✓ Docker environment built successfully")
        return True
    else:
        print(f"✗ Docker build failed: {result.stderr}")
        return False


def setup_environment(file_a, file_b):
    """
    Complete environment setup:
    1. Scan code for dependencies
    2. Create requirements.txt
    3. Build Docker environment
    """
    print(f"\n=== Environment Setup ===")
    print(f"File A: {file_a}")
    print(f"File B: {file_b}\n")

    # Step 1: Scan
    print("Step 1: Scanning code...")
    packages = scan_codebase(file_a, file_b)
    print(f"✓ Found {len(packages)} third-party packages: {', '.join(packages) if packages else 'none'}")

    # Step 2: Create requirements
    print("\nStep 2: Creating requirements file...")
    req_file = create_requirements(packages)

    # Step 3: Build Docker (optional)
    print("\nStep 3: Building Docker environment (optional)...")
    print("(Skip Docker and use local mode if you prefer)")

    docker_success = build_docker_env(req_file)

    if docker_success:
        print("\n✓ Docker environment ready!")
        print("\nRun tests in Docker:")
        print(f"  docker run --rm -v $(pwd)/src:/app/src difftest-env python /app/src/run_ab.py --a {file_a} --b {file_b} --func FUNCTION_NAME")
    else:
        print("\n⚠ Docker build failed (permissions or Docker not available)")

    # Always show local mode option
    print("\n✓ Local environment ready!")
    print("\nRun tests locally:")
    print(f"  source .venv/bin/activate")
    print(f"  pip install -r requirements_env.txt")
    print(f"  cd src")
    print(f"  python run_ab.py --a {file_a} --b {file_b} --func FUNCTION_NAME")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python simple_setup.py <file_a> <file_b>")
        sys.exit(1)

    setup_environment(sys.argv[1], sys.argv[2])
