from typing import Callable
from hypothesis import given, settings, HealthCheck
from .contracts import StrategyPlan, RunConfig, CompareResult


class ABRunner:
    def execute(
        self,
        fn_a: Callable,
        fn_b: Callable,
        strat: StrategyPlan,
        cfg: RunConfig,
    ) -> CompareResult:
        # Early-stage: stop on first counterexample (let Hypothesis shrink it).
        @settings(
            max_examples=cfg.max_examples,
            suppress_health_check=[
                HealthCheck.too_slow,
                HealthCheck.filter_too_much,
            ],
            deadline=None,
        )
        @given(strat.arg_strategy)
        def _property(args):
            from .comparator import compare

            res = compare(fn_a, fn_b, args)
            assert res.equal, res.reason or "difference"

        try:
            _property()  # raises AssertionError on difference
            return CompareResult(equal=True)
        except AssertionError as e:
            # Attempt to parse the shrunk example from the message if present; keep it simple otherwise.
            return CompareResult(equal=False, reason=str(e))
