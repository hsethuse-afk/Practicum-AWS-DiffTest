import inspect
from typing import Any, Callable
from hypothesis import strategies as st
from .contracts import StrategyPlan


class StrategySynthesizer:
    """Annotations-only strategy builder (early stage)."""

    def create_strategy(
        self, func: Callable, param_hints: dict = None
    ) -> StrategyPlan:
        try:
            sig = inspect.signature(func)
            strategies = []

            for param_name, param in sig.parameters.items():
                # First check type annotation if available
                if param.annotation != param.empty:
                    if param.annotation == int:
                        strategies.append(st.integers(-50, 50))
                    elif param.annotation == str:
                        strategies.append(st.text(max_size=10))
                    elif param.annotation == float:
                        strategies.append(st.floats(-50, 50))
                    else:
                        strategies.append(st.integers(-50, 50))
                elif param_hints and param_name in param_hints:
                    # Use provided hints as fallback
                    hint = param_hints[param_name]
                    if hint == "positive_int":
                        strategies.append(st.integers(1, 100))
                    elif hint == "string":
                        strategies.append(st.text(max_size=20))
                    elif hint == "list":
                        strategies.append(
                            st.lists(st.integers(-10, 10), max_size=10)
                        )
                    elif hint == "float":
                        strategies.append(st.floats(-100, 100))
                    else:
                        strategies.append(st.integers(-50, 50))
                else:
                    # Fallback to mixed strategy
                    strategies.append(
                        st.integers(-50, 50)
                        | st.text(max_size=10)
                        | st.floats(-50, 50)
                    )

                return (
                    StrategyPlan(arg_strategy=st.tuples(*strategies))
                    if strategies
                    else StrategyPlan(arg_strategy=st.tuples())
                )

        except Exception:
            # Fallback to basic strategy
            return StrategyPlan(
                arg_strategy=st.tuples(st.integers(-50, 50))
            )
