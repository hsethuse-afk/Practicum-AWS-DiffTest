import inspect
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Tuple,
    Set,
    Union,
    get_origin,
    get_args,
)
from decimal import Decimal
from datetime import datetime, date, time
from hypothesis import strategies as st
from .contracts import StrategyPlan
from .logger import get_logger
from .righttyper import RightTyper


class StrategySynthesizer:
    """Annotation-first strategy builder with RightTyper integration."""

    def __init__(self, use_righttyper: bool = True):
        self.log = get_logger()
        self.use_righttyper = use_righttyper
        self.righttyper = RightTyper() if use_righttyper else None

        # Enhanced registry with advanced types
        self.registry: Dict[Any, Callable[[], st.SearchStrategy]] = {
            # Basic types (expanded ranges)
            int: lambda: st.integers(min_value=-100, max_value=100),
            float: lambda: st.floats(
                min_value=-100,
                max_value=100,
                allow_nan=False,
                allow_infinity=False,
            ),
            str: lambda: st.text(max_size=20),
            bool: lambda: st.booleans(),
            bytes: lambda: st.binary(max_size=50),

            # Advanced numeric types
            complex: lambda: st.complex_numbers(
                min_magnitude=0, max_magnitude=100
            ),
            Decimal: lambda: st.decimals(
                min_value=-100, max_value=100,
                allow_nan=False, allow_infinity=False
            ),

            # Date/time types
            datetime: lambda: st.datetimes(
                min_value=datetime(2020, 1, 1),
                max_value=datetime(2025, 12, 31)
            ),
            date: lambda: st.dates(
                min_value=date(2020, 1, 1),
                max_value=date(2025, 12, 31)
            ),
            time: lambda: st.times(),

            # Enhanced Any strategy
            Any: lambda: st.one_of(
                st.integers(min_value=-100, max_value=100),
                st.floats(
                    min_value=-100,
                    max_value=100,
                    allow_nan=False,
                    allow_infinity=False,
                ),
                st.text(max_size=20),
                st.booleans(),
                st.binary(max_size=20),
            ),
        }

    def create_strategy(
        self, func: Callable, param_hints: Dict[str, Any] | None = None
    ) -> StrategyPlan:
        # Use RightTyper for optimal strategy if available
        if self.use_righttyper and self.righttyper:
            try:
                return self.righttyper.get_optimal_strategy(func)
            except Exception as e:
                self.log.debug(f"[StrategySynthesizer] RightTyper failed: {e}, falling back")

        # Fallback to original logic
        sig = inspect.signature(func)
        strategies = []
        for param in sig.parameters.values():
            strategies.append(
                self._strategy_for_param(param, param_hints or {})
            )

        return StrategyPlan(
            arg_strategy=(
                st.tuples(*strategies) if strategies else st.tuples()
            )
        )

    def _strategy_for_param(
        self, param: inspect.Parameter, hints: Dict[str, Any]
    ) -> st.SearchStrategy:
        # 1) Annotation
        if param.annotation is not inspect._empty:
            self.log.debug(
                f"[StrategySynthesizer] Using Annotation for {param.annotation}"
            )
            return self._from_annotation(param.annotation)

        # 2) Hint (either a ready-made strategy or a keyword)
        if param.name in hints:
            self.log.debug("[StrategySynthesizer] Using hints")
            return self._normalize_hint(hints[param.name])

        # 3) Default value type inference
        if param.default is not inspect._empty:
            self.log.debug("[StrategySynthesizer] Using Default Value")
            return self._from_annotation(type(param.default))

        # 4) Fallback mixed strategy
        return st.one_of(
            self.registry[int](),
            self.registry[float](),
            self.registry[str](),
        )

    def _normalize_hint(self, hint: Any) -> st.SearchStrategy:
        if isinstance(hint, st.SearchStrategy):
            return hint
        # Keyword hints kept compatible with your earlier version:
        if hint == "positive_int":
            return st.integers(min_value=1, max_value=100)
        if hint == "string":
            return st.text(max_size=20)
        if hint == "list":
            return st.lists(st.integers())
        if hint == "float":
            return st.floats(
                min_value=-100,
                max_value=100,
                allow_nan=False,
                allow_infinity=False,
            )
        # Unknown hint → safe fallback
        return self.registry[int]()

    def _from_annotation(self, annotation: Any) -> st.SearchStrategy:
        # Direct hits
        if annotation in self.registry:
            return self.registry[annotation]()

        # Handle typing.Any explicitly BEFORE from_type()
        if annotation is Any:
            return self.registry[Any]()

        origin = get_origin(annotation)
        args = get_args(annotation)

        # Normalize bare builtins: list, dict, set, tuple
        if origin is None and annotation in (list, dict, set, tuple):
            origin, args = annotation, ()

        # Containers
        if origin in (list, List):
            # Use a concrete default element type if missing
            elem_ann = args[0] if args else Any
            elem = self._from_annotation(
                elem_ann if elem_ann is not Any else int
            )
            return st.lists(elem, max_size=10)

        if origin in (set, Set):
            elem_ann = args[0] if args else Any
            elem = self._from_annotation(
                elem_ann if elem_ann is not Any else int
            )
            return st.sets(elem, max_size=10)

        if origin in (tuple, Tuple):
            if args and args[-1] is ...:  # Tuple[T, ...]
                base_ann = args[0] if args else int
                base = self._from_annotation(
                    base_ann if base_ann is not Any else int
                )
                return st.lists(base, max_size=5).map(tuple)
            if args:  # Tuple[T1, T2, ...]
                return st.tuples(
                    *(
                        self._from_annotation(
                            a if a is not Any else int
                        )
                        for a in args
                    )
                )
            return st.tuples()

        if origin in (dict, Dict):
            # Safe defaults: int keys, int values if unspecified/Any
            k_ann = args[0] if args else int
            v_ann = args[1] if len(args) > 1 else int
            k = self._from_annotation(
                k_ann if k_ann is not Any else int
            )
            v = self._from_annotation(
                v_ann if v_ann is not Any else int
            )
            return st.dictionaries(k, v, max_size=10)

        # Unions / Optional
        if origin is Union:
            non_none = [a for a in args if a is not type(None)]
            if len(non_none) == 1 and len(args) == 2:
                return st.none() | self._from_annotation(non_none[0])
            return st.one_of(*(self._from_annotation(a) for a in args))

        # Last-ditch: try Hypothesis’ type-based strategy
        try:
            return st.from_type(annotation)
        except Exception:
            # Conservative fallback that never touches `Any`
            return st.one_of(
                self.registry[int](),
                self.registry[float](),
                self.registry[str](),
            )
