from typing import Any, Dict, List
from .contracts import CompareResult, RunResult
from .logger import get_logger


class ABComparator:
    def __init__(self, output_check=True, input_check=False):
        self.output_check = output_check
        self.input_check = input_check
        self.log = get_logger()

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
                # TODO Custom Comparator, other form of compare instead of ==
                if a_result.output != b_result.output:
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
