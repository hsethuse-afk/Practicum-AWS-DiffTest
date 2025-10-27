from typing import Any, Dict, List
import numpy as np
from .contracts import CompareResult, RunResult
from .logger import get_logger


class ABComparator:
    def __init__(self, output_check=True, input_check=False):
        self.output_check = output_check
        self.input_check = input_check
        self.log = get_logger()

    def _values_equal(self, a: Any, b: Any) -> bool:
        """
        Compare two values for equality, handling special cases like NumPy arrays.

        Args:
            a: First value to compare
            b: Second value to compare

        Returns:
            True if values are equal, False otherwise
        """
        # Handle tuples (like ("ret", value) or ("exc", error))
        if isinstance(a, tuple) and isinstance(b, tuple):
            if len(a) != len(b):
                return False
            return all(self._values_equal(a_item, b_item) for a_item, b_item in zip(a, b))

        # Handle NumPy arrays
        if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
            try:
                # Use np.array_equal for proper array comparison
                # This handles NaN values correctly (NaN == NaN returns True)
                return np.array_equal(a, b, equal_nan=True)
            except Exception:
                return False

        # Handle lists
        if isinstance(a, list) and isinstance(b, list):
            if len(a) != len(b):
                return False
            return all(self._values_equal(a_item, b_item) for a_item, b_item in zip(a, b))

        # Handle dicts
        if isinstance(a, dict) and isinstance(b, dict):
            if set(a.keys()) != set(b.keys()):
                return False
            return all(self._values_equal(a[k], b[k]) for k in a.keys())

        # Default comparison for primitives and other types
        try:
            return a == b
        except Exception:
            # If comparison fails, they're not equal
            return False

    def compare(
        self, a_results: RunResult, b_results: RunResult
    ) -> CompareResult:
        self.log.verbose("[ABComparator] Comparing Results")
        mismatches: List[Dict[str, Any]] = []
        mismatches_count = 0
        successes = 0
        total = len(a_results)
        for i in range(total):
            a_result: RunResult = a_results[i]
            b_result: RunResult = b_results[i]
            local_success = True
            if self.input_check:
                # TODO
                pass
            if self.output_check:
                # Use custom comparison that handles NumPy arrays and other special types
                if not self._values_equal(a_result.output, b_result.output):
                    local_success = False
            if local_success:
                successes += 1
            else:
                mismatches_count += 1
                if len(mismatches) < 20:  # keep preview small
                    mismatches.append(
                        {
                            "args": a_result.input,
                            "A": a_result.output,
                            "B": b_result.output,
                        }
                    )

        passed = len(mismatches) == 0
        # Pick one illustrative example if any
        example = mismatches[0]["args"] if mismatches else None
        reason = (
            None
            if passed
            else "Differences observed (see mismatches preview)."
        )

        return CompareResult(
            equal=passed,
            reason=reason,
            example=example,
            stats={
                "total_examples": total,
                "successes": successes,
                "mismatches": mismatches_count,
            },
            mismatches=mismatches,
        )
