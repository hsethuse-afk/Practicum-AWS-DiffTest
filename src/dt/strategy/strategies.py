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
    Optional,
)
from hypothesis import strategies as st
from ..contracts import StrategyPlan
from ..logger import get_logger
from .strategy_config import StrategyConfig
from .instance_planner import InstanceStrategyPlanner


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
        self.instance_planner = InstanceStrategyPlanner()

    def create_strategy(
        self,
        func: Callable,
        param_types: Dict[str, Any],
        cls: Optional[type] = None,
        constructor_types: Optional[Dict[str, Any]] = None,
        max_examples: int = 200,
    ) -> StrategyPlan:
        """
        Create a strategy plan for a function from discovered parameter types.

        For class methods, also generates instance strategy.

        Args:
            func: The function/method to create strategies for
            param_types: Dictionary mapping parameter names to their types
                        (already discovered by TypeDiscoverer)
            cls: Optional class type (for class method testing)
            constructor_types: Optional constructor parameter types (for class method testing)
            max_examples: Maximum number of test examples (used for instance distribution)

        Returns:
            StrategyPlan containing the argument strategy, individual param strategies,
            and optionally instance strategy for class methods
        """
        # Generate strategies from the provided types
        sig = inspect.signature(func)
        strategies = []
        param_strategies = {}

        for param in sig.parameters.values():
            # Skip 'self' parameter for class methods
            if param.name == "self":
                continue

            param_type = param_types.get(param.name, Any)
            strategy = self._create_strategy_from_type(
                param_type, param.name
            )
            strategies.append(strategy)
            param_strategies[param.name] = strategy

        arg_strategy = st.tuples(*strategies) if strategies else st.tuples()

        # Handle class method instance generation
        instance_strategy = None
        num_instances = None

        if cls is not None and constructor_types is not None:
            # Generate instance strategy from constructor types
            instance_strategy = self._create_instance_strategy(
                cls, constructor_types
            )

            # Calculate instance distribution (pass constructor_types for smarter decisions)
            num_instances, _ = self.instance_planner.calculate_distribution(
                max_examples, constructor_types=constructor_types
            )

            self.log.verbose(
                f"[StrategySynthesizer] Created instance strategy for {cls.__name__} "
                f"({num_instances} unique instances)"
            )

        return StrategyPlan(
            arg_strategy=arg_strategy,
            param_strategies=param_strategies,
            instance_strategy=instance_strategy,
            num_instances=num_instances,
        )

    def _create_instance_strategy(
        self,
        cls: type,
        constructor_types: Dict[str, Any],
    ) -> st.SearchStrategy:
        """
        Create a Hypothesis strategy for generating instances of a class.

        Uses st.builds() to construct instances from the constructor parameters.

        Args:
            cls: The class to generate instances for
            constructor_types: Dictionary mapping constructor parameter names to their types

        Returns:
            A Hypothesis SearchStrategy that generates class instances
        """
        # If constructor has no parameters, just use st.builds(cls)
        if not constructor_types:
            self.log.verbose(
                f"[StrategySynthesizer] Creating simple instance strategy for {cls.__name__} (no constructor params)"
            )
            return st.builds(cls)

        # Generate strategies for each constructor parameter
        constructor_strategies = {}
        for param_name, param_type in constructor_types.items():
            strategy = self._create_strategy_from_type(param_type, param_name)
            constructor_strategies[param_name] = strategy

        self.log.verbose(
            f"[StrategySynthesizer] Creating instance strategy for {cls.__name__} "
            f"with parameters: {list(constructor_types.keys())}"
        )

        # Use st.builds to construct instances
        return st.builds(cls, **constructor_strategies)

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

        # Try Hypothesis' from_type() for external types and classes
        # This handles numpy.ndarray, pandas types, and other registered types
        try:
            return st.from_type(annotation)
        except Exception as e:
            self.log.debug(
                f"[StrategySynthesizer] from_type() failed for {annotation}: {e}"
            )
            # Fall through to custom class handling

        # Check if it's a custom class (user-defined type) that from_type couldn't handle
        if inspect.isclass(annotation):
            # For custom classes, try to build instances using st.builds()
            try:
                # Try to discover constructor types and create nested builds
                from ..type_inference.type_discovery import TypeDiscoverer
                discoverer = TypeDiscoverer()
                constructor_types = discoverer.discover_constructor_types(annotation)

                if constructor_types:
                    # Recursively create strategies for constructor params
                    constructor_strategies = {}
                    for param_name, param_type in constructor_types.items():
                        constructor_strategies[param_name] = self._create_strategy_from_type(
                            param_type, param_name
                        )
                    return st.builds(annotation, **constructor_strategies)
                else:
                    # No constructor params - just build with defaults
                    return st.builds(annotation)
            except Exception as e:
                self.log.debug(
                    f"[StrategySynthesizer] Failed to create builds() for {annotation.__name__}: {e}"
                )
                # Fall through to final fallback

        # Final fallback for types we can't handle
        return st.one_of(
            self.registry[int](),
            self.registry[float](),
            self.registry[str](),
        )
