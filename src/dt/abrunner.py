from typing import Callable, Any, Dict, List, Tuple
import warnings
from hypothesis import given, settings, HealthCheck, seed as hseed
from .contracts import StrategyPlan, RunConfig, CompareResult, RunResult
from .logger import get_logger


def _observe(fn: Callable, args: tuple, captured_warnings: List) -> Tuple[str, Any]:
    """
    Execute function and capture its result, capturing any warnings.

    Args:
        fn: Function to execute
        args: Arguments to pass to function
        captured_warnings: List to append captured warnings to

    Returns:
        Tuple of (status, result) where status is "ret" or "exc"
    """
    try:
        with warnings.catch_warnings(record=True) as w:
            # Cause all warnings to always be triggered
            warnings.simplefilter("always")

            result = fn(*args)

            # Record any warnings that occurred
            for warning in w:
                captured_warnings.append({
                    "message": str(warning.message),
                    "category": warning.category.__name__,
                    "filename": warning.filename,
                    "lineno": warning.lineno,
                })

            return ("ret", result)
    except Exception as e:
        return ("exc", f"{type(e).__name__}: {e}")


class ABRunner:
    def __init__(self):
        self.log = get_logger()
        self.captured_warnings: List[Dict[str, Any]] = []

    def execute(
        self,
        fn_a: Callable,
        fn_b: Callable,
        strat: StrategyPlan,
        cfg: RunConfig,
    ) -> Tuple[List[RunResult], List[RunResult], List[Dict[str, Any]]]:
        """
        Execute differential tests on two functions.

        Returns:
            Tuple of (a_results, b_results, captured_warnings)
        """
        self.log.verbose("[ABRunner] Executing Tests")
        # Shared mutable state to collect a full run
        total = {"count": 0}
        a_results: List[RunResult] = []
        b_results: List[RunResult] = []
        self.captured_warnings = []  # Reset warnings for this run

        # Optional determinism: if a seed is provided, use it
        if cfg.seed is not None:
            hseed(cfg.seed)

        @settings(
            max_examples=cfg.max_examples,
            suppress_health_check=[
                HealthCheck.too_slow,
                HealthCheck.filter_too_much,
            ],
            deadline=None,
            database=None,  # early-stage: no DB reuse
        )
        @given(strat.arg_strategy)
        def _property(args):
            # Run both sides and record the observable outcomes
            total["count"] += 1

            self.log.debug(f"[ABRunner] input {total['count']}: {args}")
            out_a = _observe(fn_a, args, self.captured_warnings)
            out_b = _observe(fn_b, args, self.captured_warnings)

            self.log.debug(
                f"[ABRunner] output {total['count']}: A {out_a}, B {out_b}"
            )

            a_results.append(RunResult(input=args, output=out_a))
            b_results.append(RunResult(input=args, output=out_b))

        # Drive generation; will not stop early
        _property()
        return a_results, b_results, self.captured_warnings
