import inspect
from typing import Any, Callable, Dict
from hypothesis import strategies as st
from ..contracts import StrategyPlan
from ..logger import get_logger
from .strategy_config import StrategyConfig
from .strategy_templates import get_template_for_type, build_strategy_from_config


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

    def create_config_from_types(
        self,
        func: Callable,
        param_types: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create a configuration dictionary from parameter types (without building strategies).

        Args:
            func: The function to create configuration for
            param_types: Dictionary mapping parameter names to their types

        Returns:
            Dictionary mapping parameter names to their strategy configurations
        """
        sig = inspect.signature(func)
        config_dict = {}

        for param in sig.parameters.values():
            param_type = param_types.get(param.name, Any)
            config = self._type_to_config(param_type)
            config_dict[param.name] = config

        return config_dict

    def create_strategy_from_config(
        self,
        func: Callable,
        strategy_config: Dict[str, Any],
        param_types: Dict[str, Any] = None,
    ) -> StrategyPlan:
        """
        Create a strategy plan from a configuration dictionary.

        Args:
            func: The function to create strategies for
            strategy_config: Configuration for each parameter
            param_types: Original parameter types (for metadata)

        Returns:
            StrategyPlan containing the argument strategy
        """
        sig = inspect.signature(func)
        strategies = []
        func_signature = {}

        for param in sig.parameters.values():
            if param.name in strategy_config:
                config = strategy_config[param.name]
                strategy = self._build_strategy_from_config(config, param.name)
                strategies.append(strategy)
                func_signature[param.name] = str(param)
            else:
                self.log.debug(f"[StrategySynthesizer] No config for parameter '{param.name}', using Any")
                strategies.append(self.registry[Any]())
                func_signature[param.name] = str(param)

        return StrategyPlan(
            arg_strategy=(
                st.tuples(*strategies) if strategies else st.tuples()
            ),
            param_types=param_types or {},
            func_signature=func_signature
        )


    def _type_to_config(self, param_type: Any) -> Dict[str, Any]:
        """
        Convert a type annotation to a configuration dictionary using templates.

        Args:
            param_type: The type annotation

        Returns:
            Configuration dictionary with type and default options from templates
        """
        return get_template_for_type(param_type)

    def _build_strategy_from_config(
        self, config: Dict[str, Any], param_name: str
    ) -> st.SearchStrategy:
        """
        Build a Hypothesis strategy from a configuration dictionary.

        Args:
            config: Configuration dictionary
            param_name: Name of the parameter (for logging)

        Returns:
            Hypothesis SearchStrategy
        """
        return build_strategy_from_config(config, param_name)

    def save_config(self, config: Dict[str, Any], filepath: str) -> None:
        """
        Save a strategy configuration to a JSON file.

        Args:
            config: Configuration dictionary
            filepath: Path to save the configuration
        """
        import json

        # Ensure .json extension
        if not filepath.endswith('.json'):
            filepath = filepath.rsplit('.', 1)[0] + '.json'

        data = {
            '_comment': 'Edit this file to customize test input generation. See Hypothesis documentation for available options.',
            'parameters': config
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        self.log.verbose(f"[StrategySynthesizer] Configuration saved to {filepath}")

    def load_config(self, filepath: str) -> Dict[str, Any]:
        """
        Load a strategy configuration from a JSON file.

        Args:
            filepath: Path to load the configuration from

        Returns:
            Configuration dictionary
        """
        import json

        # Ensure .json extension
        if not filepath.endswith('.json'):
            filepath = filepath.rsplit('.', 1)[0] + '.json'

        with open(filepath, 'r') as f:
            data = json.load(f)

        self.log.verbose(f"[StrategySynthesizer] Configuration loaded from {filepath}")
        return data.get('parameters', {})

    def print_config(self, config: Dict[str, Any]) -> None:
        """
        Print a formatted representation of a strategy configuration.

        Args:
            config: Configuration dictionary
        """
        import json
        print("\n" + "="*60)
        print("GENERATED STRATEGY CONFIGURATION")
        print("="*60)
        print(json.dumps(config, indent=2))
        print("="*60 + "\n")

    def print_strategy(self, plan: StrategyPlan) -> None:
        """
        Print a formatted representation of the strategy plan.

        Args:
            plan: The StrategyPlan to print
        """
        print("\n" + "="*60)
        print("GENERATED TEST STRATEGY")
        print("="*60)
        print(plan.pretty_print())
        print("="*60 + "\n")
