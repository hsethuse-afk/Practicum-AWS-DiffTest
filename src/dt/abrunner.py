from typing import Callable, Any, Dict, List, Tuple
from hypothesis import given, settings, HealthCheck, seed as hseed
from .contracts import StrategyPlan, RunConfig, CompareResult
from .logger import get_logger


def _observe(fn: Callable, args: tuple) -> Tuple[str, Any]:
    try:
        return ("ret", fn(*args))
    except Exception as e:
        return ("exc", f"{type(e).__name__}: {e}")


class ABRunner:
    def __init__(self):
        self.log = get_logger()

    def execute(
        self,
        fn_a: Callable,
        fn_b: Callable,
        strat: StrategyPlan,
        cfg: RunConfig,
    ) -> CompareResult:
        # Shared mutable state to collect a full run
        total = {"count": 0}
        mismatches: List[Dict[str, Any]] = []
        successes = 0

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

            self.log.verbose(
                f"[ABRunner] input {total["count"]}: {args}"
            )
            out_a = _observe(fn_a, args)
            out_b = _observe(fn_b, args)

            if out_a == out_b:
                nonlocal successes
                successes += 1
            else:
                if len(mismatches) < 20:  # keep preview small
                    mismatches.append(
                        {
                            "args": args,
                            "A": out_a,
                            "B": out_b,
                        }
                    )
            # NOTE: no assert here → Hypothesis runs all examples

        # Drive generation; will not stop early
        _property()

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
                "total_examples": total["count"],
                "successes": successes,
                "mismatches": len(mismatches),
            },
            mismatches=mismatches,
        )
