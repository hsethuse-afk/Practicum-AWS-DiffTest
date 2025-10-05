"""
Comprehensive test runner for the differential testing framework.

This module provides a TestRunner class that can run various types of tests
including JSONL differential tests, orchestrator tests, and code quality checks.
"""

import threading
from pathlib import Path
from typing import Callable, Optional

from .strategy.strategies import StrategySynthesizer
from .abrunner import ABRunner
from .results import ResultCollector
from .contracts import RunConfig, TargetPair
from ..utilities.function_extractor import (
    load_jsonl,
    extract_function_pair_from_record,
)


class TestRunner:
    """Comprehensive test runner for differential testing"""

    def __init__(self, timeout_seconds: float = 0.5):
        self.timeout_seconds = timeout_seconds
        self.synthesizer = StrategySynthesizer()
        self.runner = ABRunner()
        self.results = ResultCollector()

    def test_differential_behavior(
        self, func_a: Callable, func_b: Callable
    ) -> tuple[bool, str]:
        """Test two functions for differential behavior using ABRunner with timeout"""

        result_container = [None]

        def run_test():
            try:
                # Use existing framework classes
                strategy_plan = self.synthesizer.create_strategy(func_a)
                config = RunConfig(
                    max_examples=50
                )  # Reduced for faster execution

                # Run the comparison
                compare_result = self.runner.execute(
                    func_a, func_b, strategy_plan, config
                )

                if compare_result.equal:
                    result_container[0] = (True, "No differences found")
                else:
                    # Extract first mismatch for details
                    reason = (
                        compare_result.reason or "Differences found"
                    )
                    if compare_result.mismatches:
                        first_mismatch = compare_result.mismatches[0]
                        reason += f" (e.g., args={first_mismatch['args']}, A={first_mismatch['A']}, B={first_mismatch['B']})"
                    result_container[0] = (False, reason)

            except Exception as e:
                result_container[0] = (False, f"Unexpected error: {e}")

        # Run test in thread with timeout
        thread = threading.Thread(target=run_test)
        thread.daemon = True
        thread.start()
        thread.join(timeout=self.timeout_seconds)

        if thread.is_alive():
            return (
                False,
                f"Test timed out after {self.timeout_seconds} seconds",
            )

        return (
            result_container[0]
            if result_container[0]
            else (False, "Test completed but no result")
        )

    def run_jsonl_differential_tests(self, jsonl_path: str) -> bool:
        """Run differential tests on JSONL results file"""
        if not Path(jsonl_path).exists():
            print(f"📝 JSONL file {jsonl_path} not found, skipping")
            return True

        print(f"🔬 Running JSONL differential tests on {jsonl_path}...")

        records = load_jsonl(jsonl_path)
        print(f"  Testing {len(records)} problems...")

        passed = 0
        failed = 0

        for record in records:
            task_id = record.get("task_id", "unknown")

            try:
                # Extract functions using the utility module
                comp_func, canon_func = (
                    extract_function_pair_from_record(record)
                )

                if not comp_func or not canon_func:
                    print(
                        f"  SKIP {task_id}: Could not extract functions"
                    )
                    continue

                # Test differential behavior
                success, error = self.test_differential_behavior(
                    comp_func, canon_func
                )

                if success:
                    print(f"  PASS {task_id}")
                    passed += 1
                else:
                    print(f"  FAIL {task_id}: {error}")
                    failed += 1

            except Exception as e:
                print(f"  ERROR {task_id}: {e}")
                failed += 1

        print(f"  Summary: {passed} passed, {failed} failed")
        return failed == 0

    def set_timeout(self, timeout_seconds: float):
        """Set the timeout for individual test cases"""
        self.timeout_seconds = timeout_seconds

    def set_max_examples(self, max_examples: int):
        """Set the maximum number of examples for Hypothesis testing"""
        # This would require modifying the run_test method to accept max_examples
        # For now, it's fixed at 50 in the test_differential_behavior method
        pass
