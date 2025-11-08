"""
Strategy serialization module for saving and loading Hypothesis strategies.

This module provides functionality to serialize StrategyPlan objects to JSON
and deserialize them back, allowing strategies to be reviewed and modified
by users before test execution.
"""

import json
import re
import inspect
from typing import Any, Dict, List
from hypothesis import strategies as st
from ..contracts import StrategyPlan

# Extra strategy modules that can be optionally imported
EXTRA_STRATEGY_MODULES = {
    "numpy": "hypothesis.extra.numpy",
    "pandas": "hypothesis.extra.pandas",
    "django": "hypothesis.extra.django",
    "dpcontracts": "hypothesis.extra.dpcontracts",
    "lark": "hypothesis.extra.lark",
    "pytz": "hypothesis.extra.pytz",
}


def _import_extra_strategies(
    enable_extras: List[str] = None,
) -> Dict[str, Any]:
    """
    Import extra Hypothesis strategy modules.

    Args:
        enable_extras: List of extra modules to import (e.g., ['numpy', 'pandas']).
                      If None, attempts to import all available extras.

    Returns:
        Dictionary mapping strategy names to their implementations
    """
    extra_env = {}

    # Determine which extras to try importing
    extras_to_import = (
        enable_extras
        if enable_extras is not None
        else EXTRA_STRATEGY_MODULES.keys()
    )

    for extra_name in extras_to_import:
        if extra_name not in EXTRA_STRATEGY_MODULES:
            continue

        module_path = EXTRA_STRATEGY_MODULES[extra_name]
        try:
            # Import the module
            parts = module_path.split(".")
            module = __import__(module_path, fromlist=[parts[-1]])

            # Add all public attributes to the environment
            for attr_name in dir(module):
                if not attr_name.startswith("_"):
                    extra_env[attr_name] = getattr(module, attr_name)

        except ImportError:
            # Module not available, skip silently
            pass

    return extra_env


class StrategySerializer:
    """Handles serialization and deserialization of StrategyPlan objects."""

    def __init__(self, enable_extras: List[str] = None):
        """
        Initialize the StrategySerializer with configuration.

        Args:
            enable_extras: List of extra strategy modules to enable (e.g., ['numpy', 'pandas']).
                          If None, attempts to import all available extras.
        """
        self.enable_extras = enable_extras
        # Pre-load extra strategies once during initialization
        self._extra_strategies = _import_extra_strategies(enable_extras)
        # Cache for non-serializable strategies (those with callables, etc.)
        # Key: repr string, Value: original strategy object
        self._strategy_cache = {}

    def strategy_to_dict(
        self, plan: StrategyPlan, func: Any = None
    ) -> Dict[str, Any]:
        """
        Convert a StrategyPlan to a structured dictionary representation using introspection.

        This method uses strategy introspection to extract configuration from
        strategy objects. For class methods, also includes instance strategy.

        Args:
            plan: StrategyPlan object to serialize
            func: Optional function to extract parameter names (for fallback only)

        Returns:
            Dictionary with structured parameter-based strategy representation
        """
        parameters = {}
        instance_config = None

        # Use the individual param_strategies if available (preferred method)
        if plan.param_strategies:
            # Introspect each individual strategy directly
            for param_name, strategy in plan.param_strategies.items():
                config = StrategySerializer._introspect_strategy(
                    strategy, self._strategy_cache
                )
                parameters[param_name] = config
        else:
            # Fallback: extract from tuple strategy
            # This should rarely be used since StrategySynthesizer now provides param_strategies
            param_names = []
            if func:
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())

            # Try to extract element_strategies from tuple
            arg_strat = plan.arg_strategy
            if hasattr(arg_strat, "wrapped_strategy"):
                arg_strat = arg_strat.wrapped_strategy

            if hasattr(arg_strat, "element_strategies"):
                for i, element_strat in enumerate(
                    arg_strat.element_strategies
                ):
                    param_name = (
                        param_names[i]
                        if i < len(param_names)
                        else f"param_{i}"
                    )
                    parameters[param_name] = (
                        StrategySerializer._introspect_strategy(
                            element_strat
                        )
                    )
            else:
                # Last resort: single strategy
                param_name = (
                    param_names[0] if param_names else "param_0"
                )
                parameters[param_name] = (
                    StrategySerializer._introspect_strategy(
                        plan.arg_strategy
                    )
                )

        # Handle instance strategy for class methods
        if plan.instance_strategy:
            instance_config = {
                "strategy": StrategySerializer._introspect_strategy(
                    plan.instance_strategy, self._strategy_cache
                ),
                "num_instances": plan.num_instances,
            }

        result = {
            "_comment": "Edit this file to customize test input generation. See Hypothesis documentation for available options.",
            "parameters": parameters,
        }

        # Add instance config if present (for class methods)
        if instance_config:
            result["instance"] = instance_config
            result["_comment"] += " For class methods: 'instance' defines how test instances are created."

        return result

    # Helper methods for _introspect_strategy
    @staticmethod
    def _serialize_value(value: Any, cache: Dict[str, Any] = None) -> Any:
        """Serialize a single value (strategy, type, or primitive)."""
        if hasattr(value, "do_draw"):  # It's a strategy
            return StrategySerializer._introspect_strategy(value, cache)
        elif hasattr(value, "__module__") and hasattr(value, "__name__"):
            # It's a class/type - store as string
            if value.__module__ in ("__main__", "builtins"):
                return value.__name__
            return f"{value.__module__}.{value.__name__}"
        else:
            return value

    @staticmethod
    def _introspect_lazy_args(
        args: tuple, param_names: list, has_var_positional: bool, cache: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process positional args for LazyStrategy."""
        config = {}

        if has_var_positional and args:
            # For variadic functions like tuples(*args), collect all as list
            config["element_strategies"] = [
                StrategySerializer._serialize_value(arg, cache) for arg in args
            ]
        else:
            # Map positional args to their parameter names
            for i, arg in enumerate(args):
                param_name = param_names[i] if i < len(param_names) else f"_arg_{i}"
                config[param_name] = StrategySerializer._serialize_value(arg, cache)

        return config

    @staticmethod
    def _introspect_lazy_kwargs(
        kwargs: dict, strategy: Any, cache: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process keyword args for LazyStrategy. Returns config or _chained_method."""
        # Check if any kwargs contain callables
        has_callables = any(
            callable(v) and not hasattr(v, "do_draw") for v in kwargs.values()
        )

        if has_callables:
            # For strategies with callables (e.g., functions(like=lambda)), use repr
            repr_str = repr(strategy)
            if cache is not None:
                cache[repr_str] = strategy
            return {"type": "_chained_method", "repr": repr_str}

        # Process kwargs
        config = {}
        for key, value in kwargs.items():
            if hasattr(value, "do_draw"):  # It's a strategy
                config[key] = StrategySerializer._introspect_strategy(value, cache)
            elif (
                isinstance(value, (list, tuple))
                and value
                and hasattr(value[0], "do_draw")
            ):
                # List/tuple of strategies
                config[key] = [
                    StrategySerializer._introspect_strategy(s, cache) for s in value
                ]
            else:
                config[key] = value

        return config

    @staticmethod
    def _introspect_lazy_strategy(
        strategy: Any, cache: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Introspect a LazyStrategy."""
        func = strategy.function
        args = strategy._LazyStrategy__args
        kwargs = strategy._LazyStrategy__kwargs

        func_name = func.__name__

        # Special case: from_type() uses a lambda internally (named _from_type_deferred)
        # Detect this pattern and treat it as builds()
        # We check: lambda function + single class arg + specific function qualname pattern
        if (func_name == "<lambda>" and
            args and len(args) == 1 and
            inspect.isclass(args[0]) and
            hasattr(func, '__qualname__') and
            '_from_type' in func.__qualname__):
            func_name = "builds"

        config = {"type": func_name}

        # Special handling for builds and from_type - they have 'target' as first positional arg
        if func_name in ("builds", "from_type") and args:
            # First arg is the target class/type
            target = args[0]
            target_str = StrategySerializer._serialize_value(target, cache)
            config["target"] = target_str

            # Remaining args (if any) are processed normally
            remaining_args = args[1:]

            # Get parameter names (skip 'target' which is first param)
            try:
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())[1:]  # Skip 'target'
                has_var_positional = any(
                    p.kind == inspect.Parameter.VAR_POSITIONAL
                    for p in sig.parameters.values()
                )
            except:
                param_names = []
                has_var_positional = False

            # Process remaining args if any
            if remaining_args:
                arg_config = StrategySerializer._introspect_lazy_args(
                    remaining_args, param_names, has_var_positional, cache
                )
                config.update(arg_config)
        else:
            # Regular strategy - process args normally
            # Get parameter names from the function signature
            try:
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                has_var_positional = any(
                    p.kind == inspect.Parameter.VAR_POSITIONAL
                    for p in sig.parameters.values()
                )
            except:
                param_names = []
                has_var_positional = False

            # Process args
            arg_config = StrategySerializer._introspect_lazy_args(
                args, param_names, has_var_positional, cache
            )
            config.update(arg_config)

        # Process kwargs (may return early if has callables)
        kwarg_config = StrategySerializer._introspect_lazy_kwargs(
            kwargs, strategy, cache
        )
        if kwarg_config.get("type") == "_chained_method":
            return kwarg_config  # Early return for chained methods
        config.update(kwarg_config)

        return config

    @staticmethod
    def _introspect_direct_strategy(
        strategy: Any, cache: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Introspect a direct (non-lazy) strategy."""
        actual = strategy
        if hasattr(strategy, "wrapped_strategy"):
            actual = strategy.wrapped_strategy

        strategy_type = type(actual).__name__.replace("Strategy", "").lower()

        # Check if it's a complex strategy that should use repr
        if strategy_type in ["mapped", "filtered"]:
            return {"type": "_chained_method", "repr": repr(strategy)}

        config = {"type": strategy_type}

        # Special handling for just() - use 'value' not 'elements'
        if strategy_type == "just" and hasattr(actual, "value"):
            config["value"] = actual.value
            return config

        # Generic attribute extraction
        common_attrs = [
            "elements",
            "element_strategies",
            "min_value",
            "max_value",
            "min_size",
            "max_size",
        ]

        for attr in common_attrs:
            if hasattr(actual, attr):
                value = getattr(actual, attr)
                # Handle tuples/lists of strategies
                if (
                    isinstance(value, (tuple, list))
                    and value
                    and hasattr(value[0], "do_draw")
                ):
                    config[attr] = [
                        StrategySerializer._introspect_strategy(s, cache)
                        for s in value
                    ]
                # Handle single strategy
                elif hasattr(value, "do_draw"):
                    config[attr] = StrategySerializer._introspect_strategy(
                        value, cache
                    )
                # Handle tuples (convert to list for JSON)
                elif isinstance(value, tuple):
                    config[attr] = list(value)
                # Handle regular values
                else:
                    config[attr] = value

        return config

    @staticmethod
    def _introspect_strategy(
        strategy: Any, cache: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Introspect a strategy object to extract its configuration.

        Args:
            strategy: Hypothesis strategy object
            cache: Optional cache dict to store non-serializable strategies

        Returns:
            Dictionary with strategy configuration
        """
        # Check if it's a LazyStrategy FIRST (most common case)
        if hasattr(strategy, "function") and hasattr(
            strategy, "_LazyStrategy__args"
        ):
            return StrategySerializer._introspect_lazy_strategy(strategy, cache)

        # For non-lazy strategies
        return StrategySerializer._introspect_direct_strategy(strategy, cache)

    def dict_to_strategy(
        self, data: Dict[str, Any], extra_globals: Dict[str, Any] = None
    ) -> StrategyPlan:
        """
        Convert a structured dictionary back to a StrategyPlan.

        Handles both regular functions and class methods (with instance strategies).

        Args:
            data: Dictionary containing structured parameter configuration
            extra_globals: Additional global variables (e.g., user-defined classes)

        Returns:
            StrategyPlan object reconstructed from the dictionary
        """
        if "parameters" not in data:
            raise ValueError(
                "Invalid strategy format: missing 'parameters' key"
            )

        parameters = data["parameters"]

        # Build evaluation environment
        eval_env = st.__dict__.copy()
        eval_env["st"] = st

        # Add Python builtins needed for strategies (like tuple, list, dict)
        eval_env.update(
            {
                "tuple": tuple,
                "list": list,
                "dict": dict,
                "set": set,
                "frozenset": frozenset,
                "int": int,
                "float": float,
                "str": str,
                "bool": bool,
            }
        )

        # Add pre-loaded extra strategies
        eval_env.update(self._extra_strategies)

        if extra_globals:
            eval_env.update(extra_globals)

        # Reconstruct strategies for each parameter
        strategies = []
        param_strategies = {}

        for param_name, param_config in parameters.items():
            strategy = self._build_strategy(param_config, eval_env)
            strategies.append(strategy)
            param_strategies[param_name] = strategy

        # Create tuple strategy
        if strategies:
            arg_strategy = st.tuples(*strategies)
        else:
            arg_strategy = st.tuples()

        # Reconstruct instance strategy if present (for class methods)
        instance_strategy = None
        num_instances = None

        if "instance" in data:
            instance_config = data["instance"]
            instance_strategy = self._build_strategy(
                instance_config["strategy"], eval_env
            )
            num_instances = instance_config.get("num_instances")

        return StrategyPlan(
            arg_strategy=arg_strategy,
            param_strategies=param_strategies,
            instance_strategy=instance_strategy,
            num_instances=num_instances,
        )

    def _build_strategy(
        self, config: Any, eval_env: Dict[str, Any]
    ) -> Any:
        """
        Build a Hypothesis strategy from a structured config.

        Args:
            config: Strategy configuration (dict or primitive value)
            eval_env: Evaluation environment with available types

        Returns:
            Hypothesis strategy object or primitive value
        """
        # Handle primitive values (not strategies)
        if not isinstance(config, dict):
            return config

        # Must have a 'type' field to be a strategy
        strategy_type = config.get("type")
        if not strategy_type:
            # Not a strategy, return as-is
            return config

        # Handle chained methods (stored as repr)
        if strategy_type == "_chained_method":
            repr_str = config.get("repr", "")

            # Check cache first for non-serializable strategies (those with callables)
            if repr_str in self._strategy_cache:
                return self._strategy_cache[repr_str]

            try:
                # Use eval with the eval_env to reconstruct the chained strategy
                return eval(repr_str, {"__builtins__": {}}, eval_env)
            except Exception as e:
                raise ValueError(
                    f"Failed to evaluate chained method '{repr_str}': {e}"
                )

        # Map introspected type names to Hypothesis function names
        # The introspection produces lowercase class names (oneof, sampledfrom)
        # but Hypothesis uses underscored function names (one_of, sampled_from)
        type_mapping = {
            "oneof": "one_of",
            "sampledfrom": "sampled_from",
            "fixeddictionaries": "fixed_dictionaries",
        }

        strategy_type = type_mapping.get(strategy_type, strategy_type)

        # Get the strategy function
        if strategy_type not in eval_env:
            raise ValueError(f"Unknown strategy type: {strategy_type}")

        strategy_func = eval_env[strategy_type]

        # Build arguments for the strategy
        kwargs = {}
        args = []  # For positional arguments

        for key, value in config.items():
            if key == "type":
                continue

            # Recursively build nested values (could be strategies or primitives)
            if isinstance(value, dict) and "type" in value:
                # It's a nested strategy
                nested_strategy = self._build_strategy(value, eval_env)

                # Handle positional arguments for specific strategies
                if key == "elements" and strategy_type in (
                    "lists",
                    "sets",
                    "frozensets",
                    "sampled_from",
                ):
                    args.append(nested_strategy)
                elif key == "value" and strategy_type == "just":
                    args.append(nested_strategy)
                elif key == "keys" and strategy_type == "dictionaries":
                    kwargs["keys"] = nested_strategy
                elif (
                    key == "values" and strategy_type == "dictionaries"
                ):
                    kwargs["values"] = nested_strategy
                elif key == "strategies" and strategy_type in (
                    "one_of",
                    "tuples",
                ):
                    # Handle variadic strategies - could be single or multiple
                    if not isinstance(nested_strategy, list):
                        args.append(nested_strategy)
                    else:
                        args.extend(nested_strategy)
                else:
                    kwargs[key] = nested_strategy
            elif isinstance(value, list):
                # Handle lists of strategies (for variadic args like one_of)
                built_list = []
                for item in value:
                    if isinstance(item, dict) and "type" in item:
                        built_list.append(
                            self._build_strategy(item, eval_env)
                        )
                    else:
                        built_list.append(item)

                # For variadic strategies, unpack the list
                # Handle both 'strategies' (user-provided) and 'element_strategies'/'original_strategies' (introspected)
                if key in (
                    "strategies",
                    "element_strategies",
                    "original_strategies",
                ) and strategy_type in ("one_of", "tuples"):
                    # Skip if we already processed element_strategies (prefer it over original_strategies)
                    if (
                        key == "original_strategies"
                        and "element_strategies" in config
                    ):
                        continue
                    args.extend(built_list)
                else:
                    kwargs[key] = built_list
            # Handle special 'target' field for from_type and builds
            elif key == "target":
                # Resolve the target type from eval_env
                resolved_type = self._resolve_type(value, eval_env)
                if strategy_type in ("from_type", "builds"):
                    args.insert(
                        0, resolved_type
                    )  # target is first positional arg
                else:
                    kwargs[key] = resolved_type
            # Handle positional primitives (like just(True))
            elif key == "value" and strategy_type == "just":
                args.append(value)
            elif key == "elements" and strategy_type in (
                "sampled_from",
            ):
                args.append(value)
            else:
                # Primitive value as keyword arg
                kwargs[key] = value

        # Call the strategy function with the arguments
        try:
            if args:
                return strategy_func(*args, **kwargs)
            else:
                return strategy_func(**kwargs)
        except Exception as e:
            raise ValueError(
                f"Failed to build strategy '{strategy_type}' with args {args}, kwargs {kwargs}: {e}"
            )

    def _resolve_type(
        self, type_str: str, eval_env: Dict[str, Any]
    ) -> Any:
        """
        Resolve a type string to an actual type object.

        Args:
            type_str: Type string like "numpy.ndarray", "Point", or "typing.Callable[..., int]"
            eval_env: Evaluation environment

        Returns:
            The actual type/class object
        """
        # Handle complex type annotations with brackets (e.g., typing.Callable[..., int])
        if "[" in type_str and "]" in type_str:
            # These need to be evaluated, not just attribute-accessed
            try:
                return eval(type_str, {"__builtins__": {}}, eval_env)
            except Exception as e:
                raise ValueError(
                    f"Cannot resolve type '{type_str}': {e}"
                )

        # Handle module.Type notation (e.g., numpy.ndarray, a1.Point)
        if "." in type_str:
            parts = type_str.split(".")

            # First try to resolve the full module path
            obj = eval_env.get(parts[0])
            if obj is not None:
                # Module found, navigate to the type
                for part in parts[1:]:
                    obj = getattr(obj, part)
                return obj

            # If module not found, try just the class name (for same-module classes)
            # E.g., "a1.Point" might just be "Point" in the eval_env
            class_name = parts[-1]
            if class_name in eval_env:
                return eval_env[class_name]

            # Still not found, raise error
            raise ValueError(
                f"Cannot resolve type '{type_str}': tried '{parts[0]}' module and '{class_name}' class, neither found"
            )
        else:
            # Simple name lookup (e.g., Point)
            if type_str not in eval_env:
                raise ValueError(
                    f"Cannot resolve type '{type_str}': not found in environment"
                )
            return eval_env[type_str]

    def save_to_file(
        self, plan: StrategyPlan, filepath: str, func: Any = None
    ) -> None:
        """
        Save a StrategyPlan to a JSON file.

        Args:
            plan: StrategyPlan to save
            filepath: Path to save the JSON file
            func: Optional function to extract parameter names
        """
        data = self.strategy_to_dict(plan, func)

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def load_from_file(
        self, filepath: str, extra_globals: Dict[str, Any] = None
    ) -> StrategyPlan:
        """
        Load a StrategyPlan from a JSON file.

        Args:
            filepath: Path to the JSON file
            extra_globals: Additional global variables (e.g., user-defined classes)

        Returns:
            StrategyPlan object loaded from file
        """
        with open(filepath, "r") as f:
            data = json.load(f)

        return self.dict_to_strategy(data, extra_globals)
