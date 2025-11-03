import inspect
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
from ..contracts import StrategyPlan
from ..logger import get_logger
from .strategy_config import StrategyConfig


class StrategySynthesizer:
    """
    Strategy builder that generates Hypothesis strategies from type information.

    This class is responsible ONLY for converting types to Hypothesis strategies.
    Type discovery is handled separately by TypeDiscoverer in the Orchestrator.

    The default strategy values can be customized by passing a config class.
    See strategy_config.py for configuration options.
    """

    def __init__(self, config: type = StrategyConfig):
        self.log = get_logger()
        self.config = config
        self.registry = config.get_registry()

    def create_strategy(
        self,
        func: Callable,
        param_types: Dict[str, Any],
    ) -> StrategyPlan:
        """
        Create a strategy plan for a function from discovered parameter types.

        Args:
            func: The function to create strategies for
            param_types: Dictionary mapping parameter names to their types
                        (already discovered by TypeDiscoverer)

        Returns:
            StrategyPlan containing the argument strategy and individual param strategies
        """
        # Generate strategies from the provided types
        sig = inspect.signature(func)
        strategies = []
        param_strategies = {}

        for param in sig.parameters.values():
            param_type = param_types.get(param.name, Any)
            strategy = self._create_strategy_from_type(
                param_type, param.name
            )
            strategies.append(strategy)
            param_strategies[param.name] = strategy

        return StrategyPlan(
            arg_strategy=(
                st.tuples(*strategies) if strategies else st.tuples()
            ),
            param_strategies=param_strategies
        )

    def _create_strategy_from_type(
        self, param_type: Any, param_name: str
    ) -> st.SearchStrategy:
        """
        Create a Hypothesis strategy from a type object.

        Note: TypeDiscoverer ensures all types are resolved to actual type objects,
        so this method should NEVER receive strings.

        Args:
            param_type: The type object to create a strategy for
            param_name: The parameter name (for logging)

        Returns:
            A Hypothesis SearchStrategy
        """
        # Sanity check - strings should be resolved by TypeDiscoverer
        if isinstance(param_type, str):
            self.log.debug(
                f"[StrategySynthesizer] Received unexpected string type '{param_type}' for '{param_name}' - using fallback"
            )
            return self._fallback_strategy()

        # Handle ready-made strategies
        if isinstance(param_type, st.SearchStrategy):
            return param_type

        # Handle type annotations (the main path)
        return self._from_annotation(param_type)

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
