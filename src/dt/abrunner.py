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
        Execute differential tests on two functions or class methods.

        For class methods, generates instances and distributes tests across them.

        Returns:
            Tuple of (a_results, b_results, captured_warnings)
        """
        self.log.verbose("[ABRunner] Executing Tests")

        # Check if we're testing class methods (instance strategy present)
        if strat.instance_strategy and strat.num_instances:
            return self._execute_class_methods(fn_a, fn_b, strat, cfg)
        else:
            return self._execute_functions(fn_a, fn_b, strat, cfg)

    def _execute_functions(
        self,
        fn_a: Callable,
        fn_b: Callable,
        strat: StrategyPlan,
        cfg: RunConfig,
    ) -> Tuple[List[RunResult], List[RunResult], List[Dict[str, Any]]]:
        """Execute tests for regular functions."""
        # Shared mutable state to collect a full run
        total = {"count": 0}
        a_results: List[RunResult] = []
        b_results: List[RunResult] = []
        self.captured_warnings = []  # Reset warnings for this run

        # Define the test property
        def make_property():
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

            return _property

        # Apply seed decorator if provided
        if cfg.seed is not None:
            _property = hseed(cfg.seed)(make_property())
        else:
            _property = make_property()

        # Drive generation; will not stop early
        _property()
        return a_results, b_results, self.captured_warnings

    def _execute_class_methods(
        self,
        method_a: Callable,
        method_b: Callable,
        strat: StrategyPlan,
        cfg: RunConfig,
    ) -> Tuple[List[RunResult], List[RunResult], List[Dict[str, Any]]]:
        """
        Execute tests for class methods with instance generation.

        Generates unique instances and distributes tests across them.
        """
        from hypothesis import strategies as st

        total = {"count": 0}
        a_results: List[RunResult] = []
        b_results: List[RunResult] = []
        self.captured_warnings = []

        # Calculate examples per instance
        examples_per_instance = cfg.max_examples // strat.num_instances

        self.log.verbose(
            f"[ABRunner] Testing class methods: {strat.num_instances} instances, "
            f"{examples_per_instance} examples per instance"
        )

        # Generate instances upfront (for controlled distribution)
        from hypothesis import find

        instances = []
        generation_errors = []
        for i in range(strat.num_instances):
            try:
                # Generate a unique instance
                instance = strat.instance_strategy.example()
                instances.append(instance)
                self.log.debug(f"[ABRunner] Generated instance {i+1}: {instance}")
            except Exception as e:
                # Track the error for reporting
                generation_errors.append((i+1, e))
                self.log.debug(
                    f"[ABRunner] Failed to generate instance {i+1}: {e}"
                )
                # Continue with fewer instances if generation fails
                break

        if not instances:
            error_msg = (
                "[ABRunner] No instances generated, cannot test class methods. "
                "Instance generation failed. "
            )
            if generation_errors:
                first_error = generation_errors[0]
                error_msg += (
                    f"First error (instance {first_error[0]}): {first_error[1]}. "
                    "This usually means the constructor has constraints that aren't reflected in the strategy. "
                    "Edit the strategy JSON file to add constraints (e.g., min_value=1 for positive integers)."
                )
            self.log.verbose(error_msg)
            print(f"\n⚠️  {error_msg}\n")

            # Add execution error to warnings for HTML report
            self.captured_warnings.append({
                "message": error_msg,
                "category": "ExecutionError",
                "filename": "<test_execution>",
                "lineno": 0,
            })

            return a_results, b_results, self.captured_warnings

        # Test each instance with its allocated examples
        for instance_idx, instance in enumerate(instances):
            self.log.debug(
                f"[ABRunner] Testing instance {instance_idx+1}/{len(instances)}"
            )

            # Define test property for this instance
            def make_property():
                @settings(
                    max_examples=examples_per_instance,
                    suppress_health_check=[
                        HealthCheck.too_slow,
                        HealthCheck.filter_too_much,
                    ],
                    deadline=None,
                    database=None,
                )
                @given(strat.arg_strategy)
                def _property(args):
                    total["count"] += 1

                    # Prepend instance to args (method call: instance.method(*args))
                    # For unbound method call: method(instance, *args)
                    full_args = (instance,) + args

                    self.log.debug(
                        f"[ABRunner] input {total['count']}: instance={instance}, args={args}"
                    )

                    out_a = _observe(method_a, full_args, self.captured_warnings)
                    out_b = _observe(method_b, full_args, self.captured_warnings)

                    self.log.debug(
                        f"[ABRunner] output {total['count']}: A {out_a}, B {out_b}"
                    )

                    # Store results with full args (including instance)
                    a_results.append(RunResult(input=full_args, output=out_a))
                    b_results.append(RunResult(input=full_args, output=out_b))

                return _property

            # Apply seed decorator if provided (only for first instance)
            if cfg.seed is not None and instance_idx == 0:
                _property = hseed(cfg.seed)(make_property())
            else:
                _property = make_property()

            _property()

        return a_results, b_results, self.captured_warnings
