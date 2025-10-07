#!/usr/bin/env python3
"""
Dynamic differential testing script that auto-discovers functions
"""

import importlib.util
import inspect
import sys


def load_module(file_path):
    """Load a Python module from file path."""
    spec = importlib.util.spec_from_file_location("module", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def discover_functions(module):
    """Discover all callable functions in a module (excluding private and imports)."""
    functions = {}
    for name, obj in inspect.getmembers(module):
        if inspect.isfunction(obj) and not name.startswith('_') and obj.__module__ == module.__name__:
            functions[name] = obj
    return functions


def generate_test_inputs(func, num_tests=3):
    """Generate basic test inputs based on function signature."""
    sig = inspect.signature(func)
    params = list(sig.parameters.values())

    test_inputs = []

    # Generate simple test cases based on parameter count
    if len(params) == 0:
        test_inputs = [() for _ in range(num_tests)]
    elif len(params) == 1:
        # Single parameter - try different types
        test_inputs = [
            ([1, 2, 3, 4, 5],),
            ([10, 20, 30],),
            ([100, 200, 300, 400],),
        ]
    elif len(params) == 2:
        # Two parameters
        test_inputs = [
            ([[1, 2], [3, 4]], [[5, 6], [7, 8]]),
            ([[1, 0], [0, 1]], [[2, 3], [4, 5]]),
            ([1, 2, 3], [4, 5, 6]),
        ]
    else:
        # Multiple parameters - generate tuples
        for i in range(num_tests):
            test_inputs.append(tuple([i+j for j in range(len(params))]))

    return test_inputs


def test_function_pair(func_a, func_b, func_name):
    """Test a pair of functions with auto-generated inputs."""
    print(f"\nTest Function: {func_name}")
    print("-" * 60)

    # Generate test inputs
    test_cases = generate_test_inputs(func_a)

    matches = 0
    differences = []
    errors = 0

    for i, test_input in enumerate(test_cases, 1):
        try:
            # Call functions with test input
            if isinstance(test_input, tuple) and len(test_input) > 0:
                result_a = func_a(*test_input)
                result_b = func_b(*test_input)
            else:
                result_a = func_a()
                result_b = func_b()

            # Compare results (handle numpy arrays and other types)
            try:
                import numpy as np
                if isinstance(result_a, np.ndarray) and isinstance(result_b, np.ndarray):
                    are_equal = np.array_equal(result_a, result_b)
                elif isinstance(result_a, dict) and isinstance(result_b, dict):
                    are_equal = result_a == result_b
                else:
                    are_equal = result_a == result_b
            except ImportError:
                are_equal = result_a == result_b

            if are_equal:
                matches += 1
                print(f"  Test {i}: ✓ MATCH")
            else:
                differences.append((test_input, result_a, result_b))
                print(f"  Test {i}: ✗ DIFF")
                print(f"    Input: {test_input}")
                print(f"    A: {result_a}")
                print(f"    B: {result_b}")

        except Exception as e:
            errors += 1
            print(f"  Test {i}: ✗ ERROR - {e}")

    print(f"\nResult: {matches} matches, {len(differences)} differences, {errors} errors")
    return matches, differences, errors


def main():
    print("=" * 60)
    print("DYNAMIC DIFFERENTIAL TESTING")
    print("=" * 60)
    print("\nAuto-discovering functions in code_a.py and code_b.py...")

    # Load both modules
    try:
        module_a = load_module("code_a.py")
        module_b = load_module("code_b.py")
    except Exception as e:
        print(f"ERROR: Could not load modules - {e}")
        sys.exit(1)

    # Discover functions
    functions_a = discover_functions(module_a)
    functions_b = discover_functions(module_b)

    print(f"\nFound {len(functions_a)} functions in code_a.py: {list(functions_a.keys())}")
    print(f"Found {len(functions_b)} functions in code_b.py: {list(functions_b.keys())}")

    # Find common functions
    common_functions = set(functions_a.keys()) & set(functions_b.keys())

    if not common_functions:
        print("\n⚠ WARNING: No common functions found between the two files!")
        sys.exit(0)

    print(f"\nTesting {len(common_functions)} common functions: {sorted(common_functions)}")
    print("=" * 60)

    # Test each common function
    total_matches = 0
    total_diffs = 0
    total_errors = 0

    for func_name in sorted(common_functions):
        func_a = functions_a[func_name]
        func_b = functions_b[func_name]

        matches, diffs, errors = test_function_pair(func_a, func_b, func_name)
        total_matches += matches
        total_diffs += len(diffs)
        total_errors += errors

    # Summary
    print("\n" + "=" * 60)
    print("TESTING COMPLETE")
    print("=" * 60)
    print(f"Total: {total_matches} matches, {total_diffs} differences, {total_errors} errors")
    print("=" * 60)


if __name__ == '__main__':
    main()
