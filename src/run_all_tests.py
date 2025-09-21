#!/usr/bin/env python3
"""
Comprehensive test runner for the Hypothesis-based differential testing tool.

This script runs all types of tests in the project:
- Pytest unit tests (if tests/ directory exists)
- Hypothesis differential tests using the orchestrator framework
- Batch differential tests on JSONL result files
- Doctests in Python modules
- Code quality checks (ruff, mypy)

Usage:
    python run_all_tests.py [options]
    python run_all_tests.py --jsonl-results testsample/samples.jsonl_results.jsonl
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

# Import the differential testing framework
from dt.orchestrator import Orchestrator
from dt.test_runner import TestRunner


class ComprehensiveTestRunner:
    """Main test runner class that orchestrates different types of tests"""

    def __init__(self):
        self.test_runner = TestRunner(timeout_seconds=0.5)
        self.orchestrator = Orchestrator()

    def run_pytest_tests(self):
        """Run pytest tests if tests directory exists."""
        tests_dir = Path("tests")
        if tests_dir.exists():
            print("🧪 Running pytest tests...")
            result = subprocess.run(["python", "-m", "pytest", "tests/", "-v"],
                                  capture_output=False)
            return result.returncode == 0
        else:
            print("📝 No tests/ directory found, skipping pytest tests")
            return True

    def run_orchestrator_differential_tests(self):
        """Run differential tests using the orchestrator framework."""
        print("🔍 Running orchestrator differential tests...")

        # Test the palindrome functions in testsample/
        testsample_dir = Path("testsample")
        if testsample_dir.exists() and (testsample_dir / "a.py").exists() and (testsample_dir / "b.py").exists():
            print("  Testing palindrome functions (a.py vs b.py)...")
            try:
                result = self.orchestrator.run_pair(
                    "testsample/a.py",
                    "testsample/b.py",
                    "make_palindrome",
                    max_examples=50
                )
                return result is not None
            except Exception as e:
                print(f"    ❌ Differential test failed: {e}")
                return False
        else:
            print("  No sample test files found in testsample/")
            return True

    def run_jsonl_differential_tests(self, jsonl_path: str):
        """Run differential tests on JSONL results file using TestRunner."""
        return self.test_runner.run_jsonl_differential_tests(jsonl_path)

    def run_doctests(self):
        """Run doctests on modules that contain them."""
        print("📚 Running doctests...")

        success = True

        # Check testsample files for doctests
        for py_file in Path("testsample").glob("*.py"):
            if py_file.name != "__init__.py":
                print(f"  Running doctests for {py_file}...")
                result = subprocess.run([
                    "python", "-m", "doctest", str(py_file), "-v"
                ], capture_output=True, text=True)

                if result.returncode != 0:
                    print(f"    ❌ Doctests failed for {py_file}")
                    print(result.stdout)
                    print(result.stderr)
                    success = False
                else:
                    print(f"    ✅ Doctests passed for {py_file}")

        return success

    def run_linting(self):
        """Run code quality checks."""
        print("🧹 Running code quality checks...")

        success = True

        # Run ruff linting
        print("  Running ruff linting...")
        result = subprocess.run(["python", "-m", "ruff", "check", "src/"],
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("    ❌ Ruff linting failed:")
            print(result.stdout)
            success = False
        else:
            print("    ✅ Ruff linting passed")

        # Run mypy type checking
        print("  Running mypy type checking...")
        result = subprocess.run(["python", "-m", "mypy", "src/"],
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("    ❌ Type checking failed:")
            print(result.stdout)
            success = False
        else:
            print("    ✅ Type checking passed")

        return success

def main():
    parser = argparse.ArgumentParser(description="Run all tests for the differential testing tool")
    parser.add_argument("--skip-lint", action="store_true",
                       help="Skip linting and type checking")
    parser.add_argument("--skip-doctests", action="store_true",
                       help="Skip running doctests")
    parser.add_argument("--skip-diff-tests", action="store_true",
                       help="Skip orchestrator differential tests")
    parser.add_argument("--skip-pytest", action="store_true",
                       help="Skip pytest tests")
    parser.add_argument("--jsonl-results", type=str,
                       help="Path to JSONL results file for batch differential testing")

    args = parser.parse_args()

    print("🚀 Starting comprehensive test suite...")
    print("=" * 50)

    # Change to src directory for relative imports
    original_dir = os.getcwd()
    src_dir = Path("src")
    if src_dir.exists():
        os.chdir(src_dir)

    success = True

    try:
        # Initialize the test runner
        runner = ComprehensiveTestRunner()

        # Run pytest tests
        if not args.skip_pytest:
            if not runner.run_pytest_tests():
                success = False
            print()

        # Run doctests
        if not args.skip_doctests:
            if not runner.run_doctests():
                success = False
            print()

        # Run orchestrator differential tests
        if not args.skip_diff_tests:
            if not runner.run_orchestrator_differential_tests():
                success = False
            print()

        # Run JSONL differential tests if specified
        if args.jsonl_results:
            if not runner.run_jsonl_differential_tests(args.jsonl_results):
                success = False
            print()

        # Run linting and type checking
        if not args.skip_lint:
            if not runner.run_linting():
                success = False
            print()

        print("=" * 50)
        if success:
            print("🎉 All tests passed successfully!")
            return 0
        else:
            print("❌ Some tests failed. Please check the output above.")
            return 1

    finally:
        # Return to original directory
        os.chdir(original_dir)


if __name__ == "__main__":
    sys.exit(main())