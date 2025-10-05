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
    Optional,
    get_origin,
    get_args,
)
from hypothesis import strategies as st
from ..contracts import StrategyPlan
from ..logger import get_logger
from .type_discovery import TypeDiscoverer
from .strategy_config import StrategyConfig


class StrategySynthesizer:
    """
    Strategy builder that generates Hypothesis strategies from type information.

    The default strategy values can be customized by passing a config class.
    See strategy_config.py for configuration options.
    """

    def __init__(
        self,
        type_discoverer: Optional[TypeDiscoverer] = None,
        config: type = StrategyConfig,
    ):
        self.log = get_logger()
        self.type_discoverer = type_discoverer or TypeDiscoverer()
        self.config = config
        self.registry = config.get_registry()

    def create_strategy(
        self,
        func: Callable,
        param_hints: Optional[Dict[str, Any]] = None,
        test_file: Optional[str] = None,
    ) -> StrategyPlan:
        """
        Create a strategy plan for a function.

        Args:
            func: The function to create strategies for
            param_hints: Optional manual type hints
            test_file: Optional path to test file for RightTyper inference

        Returns:
            StrategyPlan containing the argument strategy
        """
        # Discover types for all parameters
        param_types = self.type_discoverer.discover_param_types(
            func, test_file, param_hints
        )

        # Generate strategies from the discovered types
        sig = inspect.signature(func)
        strategies = []
        for param in sig.parameters.values():
            param_type = param_types.get(param.name, Any)
            strategy = self._create_strategy_from_type(
                param_type, param.name
            )
            strategies.append(strategy)

        return StrategyPlan(
            arg_strategy=(
                st.tuples(*strategies) if strategies else st.tuples()
            )
        )

    def _create_strategy_from_type(
        self, param_type: Any, param_name: str
    ) -> st.SearchStrategy:
        """
        Create a Hypothesis strategy from a type.

        Args:
            param_type: The type to create a strategy for
            param_name: The parameter name (for logging)

        Returns:
            A Hypothesis SearchStrategy
        """
        # Handle string types from RightTyper
        if isinstance(param_type, str):
            return self._from_type_string(param_type)

        # Handle ready-made strategies
        if isinstance(param_type, st.SearchStrategy):
            return param_type

        # Handle keyword hints
        if param_type in ["positive_int", "string", "list", "float"]:
            return self._normalize_hint(param_type)

        # Handle type annotations
        return self._from_annotation(param_type)

    def _from_type_string(self, type_str: str) -> st.SearchStrategy:
        """
        Convert a type string to a Hypothesis strategy.

        Args:
            type_str: Type as a string (e.g., "str", "int", "list[int]")

        Returns:
            A Hypothesis SearchStrategy
        """
        import re

        # Handle basic types
        basic_type_map = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
        }

        if type_str in basic_type_map:
            return self._from_annotation(basic_type_map[type_str])

        # Parse list[T] pattern
        list_match = re.match(r"list\[(.+)\]", type_str)
        if list_match:
            elem_type_str = list_match.group(1)
            elem_strategy = self._from_type_string(elem_type_str)
            self.log.verbose(
                f"[StrategySynthesizer] Parsed type string 'list[{elem_type_str}]' -> lists({elem_strategy})"
            )
            return st.lists(
                elem_strategy, max_size=self.config.LIST_MAX_SIZE
            )

        # Parse set[T] pattern
        set_match = re.match(r"set\[(.+)\]", type_str)
        if set_match:
            elem_type_str = set_match.group(1)
            elem_strategy = self._from_type_string(elem_type_str)
            return st.sets(
                elem_strategy, max_size=self.config.SET_MAX_SIZE
            )

        # Parse dict[K, V] pattern
        dict_match = re.match(r"dict\[(.+),\s*(.+)\]", type_str)
        if dict_match:
            key_type_str = dict_match.group(1)
            val_type_str = dict_match.group(2)
            key_strategy = self._from_type_string(key_type_str)
            val_strategy = self._from_type_string(val_type_str)
            return st.dictionaries(
                key_strategy,
                val_strategy,
                max_size=self.config.DICT_MAX_SIZE,
            )

        # Parse tuple[T1, T2, ...] pattern
        tuple_match = re.match(r"tuple\[(.+)\]", type_str)
        if tuple_match:
            elements_str = tuple_match.group(1)
            if elements_str.endswith(", ..."):
                # Variable length tuple: tuple[int, ...]
                elem_type_str = elements_str[:-5].strip()
                elem_strategy = self._from_type_string(elem_type_str)
                return st.lists(
                    elem_strategy, max_size=self.config.TUPLE_MAX_SIZE
                ).map(tuple)
            else:
                # Fixed length tuple: tuple[int, str, bool]
                elem_types = [
                    t.strip() for t in elements_str.split(",")
                ]
                elem_strategies = [
                    self._from_type_string(t) for t in elem_types
                ]
                return st.tuples(*elem_strategies)

        # Bare containers without type parameters
        if type_str == "list":
            return st.lists(
                self.registry[int](), max_size=self.config.LIST_MAX_SIZE
            )
        if type_str == "dict":
            return st.dictionaries(
                self.registry[int](),
                self.registry[int](),
                max_size=self.config.DICT_MAX_SIZE,
            )
        if type_str == "set":
            return st.sets(
                self.registry[int](), max_size=self.config.SET_MAX_SIZE
            )
        if type_str == "tuple":
            return st.tuples()

        # For complex types we can't parse (e.g., "Callable[[str], bool]")
        self.log.debug(
            f"[StrategySynthesizer] Complex type string '{type_str}' - using fallback"
        )
        return self.registry[Any]()

    def _normalize_hint(self, hint: Any) -> st.SearchStrategy:
        if isinstance(hint, st.SearchStrategy):
            return hint
        # Keyword hints - use config for values
        return self.config.get_keyword_strategy(hint)

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
            return st.lists(elem, max_size=self.config.LIST_MAX_SIZE)

        if origin in (set, Set):
            elem_ann = args[0] if args else Any
            elem = self._from_annotation(
                elem_ann if elem_ann is not Any else int
            )
            return st.sets(elem, max_size=self.config.SET_MAX_SIZE)

        if origin in (tuple, Tuple):
            if args and args[-1] is ...:  # Tuple[T, ...]
                base_ann = args[0] if args else int
                base = self._from_annotation(
                    base_ann if base_ann is not Any else int
                )
                return st.lists(
                    base, max_size=self.config.TUPLE_MAX_SIZE
                ).map(tuple)
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
            return st.dictionaries(
                k, v, max_size=self.config.DICT_MAX_SIZE
            )

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
