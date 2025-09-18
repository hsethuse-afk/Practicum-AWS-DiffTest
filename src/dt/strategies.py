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
from hypothesis import strategies as st
from .contracts import StrategyPlan


class StrategySynthesizer:
    """Annotation-first strategy builder with a pluggable registry."""

    def __init__(self):
        # Simple registry for direct types; extend as needed.
        self.registry: Dict[Any, Callable[[], st.SearchStrategy]] = {
            int: lambda: st.integers(min_value=-50, max_value=50),
            float: lambda: st.floats(
                min_value=-50,
                max_value=50,
                allow_nan=False,
                allow_infinity=False,
            ),
            str: lambda: st.text(max_size=10),
            bool: lambda: st.booleans(),
        }

    def create_strategy(
        self, func: Callable, param_hints: Dict[str, Any] | None = None
    ) -> StrategyPlan:
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
            return self._from_annotation(param.annotation)

        # 2) Hint (either a ready-made strategy or a keyword)
        if param.name in hints:
            return self._normalize_hint(hints[param.name])

        # 3) Default value type inference
        if param.default is not inspect._empty:
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
            return st.lists(
                st.integers(min_value=-10, max_value=10), max_size=10
            )
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
        # Direct hits via registry
        if annotation in self.registry:
            return self.registry[annotation]()

        origin = get_origin(annotation)
        args = get_args(annotation)

        # typing aliases
        if origin in (list, List):
            elem = args[0] if args else Any
            return st.lists(self._from_annotation(elem), max_size=10)

        if origin in (tuple, Tuple):
            if args and args[-1] is ...:  # Tuple[T, ...]
                return st.lists(
                    self._from_annotation(args[0]), max_size=5
                ).map(tuple)
            if args:  # Tuple[T1, T2, ...]
                return st.tuples(
                    *(self._from_annotation(a) for a in args)
                )
            return st.tuples()  # Tuple[()] edge case

        if origin in (set, Set):
            elem = args[0] if args else Any
            return st.sets(self._from_annotation(elem), max_size=10)

        if origin in (dict, Dict):
            k = self._from_annotation(args[0] if args else Any)
            v = self._from_annotation(args[1] if len(args) > 1 else Any)
            return st.dictionaries(k, v, max_size=10)

        # Optional[T] = Union[T, NoneType], or general Union
        if origin is Union:
            # filter out NoneType for Optional
            non_none = [a for a in args if a is not type(None)]
            if len(non_none) == 1 and len(args) == 2:
                return st.none() | self._from_annotation(non_none[0])
            return st.one_of(*(self._from_annotation(a) for a in args))

        # Last-ditch: let Hypothesis infer if it can, else mixed fallback
        try:
            return st.from_type(annotation)
        except Exception:
            return st.one_of(
                self.registry[int](),
                self.registry[float](),
                self.registry[str](),
            )
