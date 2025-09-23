from typing import Callable, Any, Dict, List, Tuple
from hypothesis import given, settings, HealthCheck, seed as hseed
from .contracts import StrategyPlan, RunConfig, CompareResult, RunResult
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
    ) -> Tuple[List[RunResult], List[RunResult]]:
        self.log.verbose("[ABRunner] Executing Tests")
        # Shared mutable state to collect a full run
        total = {"count": 0}
        a_results: List[RunResult] = []
        b_results: List[RunResult] = []

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

            self.log.debug(f"[ABRunner] input {total["count"]}: {args}")
            out_a = _observe(fn_a, args)
            out_b = _observe(fn_b, args)

            self.log.debug(
                f"[ABRunner] output {total["count"]}: A {out_a}, B {out_b}"
            )

            a_results.append(RunResult(input=args, output=out_a))
            b_results.append(RunResult(input=args, output=out_b))

        # Drive generation; will not stop early
        _property()
        return a_results, b_results
