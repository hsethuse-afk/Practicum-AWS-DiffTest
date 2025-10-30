"""
Strategy templates with all possible Hypothesis configuration options.

These templates define the complete set of customizable options for each
strategy type, making it easy for users to see what can be modified.
"""

from hypothesis import strategies as st


# Mapping from config type to Hypothesis strategy builder
# The key 'type' is reserved and will be removed before passing kwargs
STRATEGY_BUILDERS = {
    'int': st.integers,
    'float': st.floats,
    'str': st.text,
    'bool': st.booleans,
    'bytes': st.binary,
    'list': st.lists,
    'dict': st.dictionaries,
    'set': st.sets,
    'tuple': st.tuples,  # Special handling needed for fixed vs variable length
    # Note: 'optional', 'union', 'any', 'from_type' need special handling
}


# Template definitions with all available Hypothesis options and default values
STRATEGY_TEMPLATES = {
    'int': {
        'type': 'int',
        'min_value': -50,  # Minimum value (inclusive)
        'max_value': 50,  # Maximum value (inclusive)
    },

    'float': {
        'type': 'float',
        'min_value': -50.0,  # Minimum value (inclusive or exclusive based on exclude_min)
        'max_value': 50.0,  # Maximum value (inclusive or exclusive based on exclude_max)
        'allow_nan': False,  # Whether to generate NaN values
        'allow_infinity': False,  # Whether to generate infinity values
        # Advanced options (usually not needed):
        # 'width': 64,  # 16, 32, or 64 - for specific float widths
        # 'exclude_min': False,  # Exclude the minimum value
        # 'exclude_max': False,  # Exclude the maximum value
    },

    'str': {
        'type': 'str',
        'min_size': 0,  # Minimum string length
        'max_size': 10,  # Maximum string length
        # Advanced options:
        # 'alphabet': None,  # String of allowed characters, or st.characters() strategy
    },

    'bool': {
        'type': 'bool'
        # No configuration options
    },

    'bytes': {
        'type': 'bytes',
        'min_size': 0,  # Minimum length
        'max_size': 10,  # Maximum length
    },

    'list': {
        'type': 'list',
        'element': None,  # Nested strategy config for list elements
        'min_size': 0,  # Minimum list length
        'max_size': 10,  # Maximum list length
        # Advanced options:
        # 'unique': False,  # Whether elements should be unique (creates unique_by effect)
    },

    'dict': {
        'type': 'dict',
        'keys': None,  # Nested strategy config for dictionary keys
        'values': None,  # Nested strategy config for dictionary values
        'min_size': 0,  # Minimum number of key-value pairs
        'max_size': 10,  # Maximum number of key-value pairs
    },

    'set': {
        'type': 'set',
        'element': None,  # Nested strategy config for set elements
        'min_size': 0,  # Minimum set size
        'max_size': 10,  # Maximum set size
    },

    'tuple': {
        'type': 'tuple',
        # For fixed-length tuples, use:
        'elements': None,  # List of strategy configs, one per element
        # OR for variable-length tuples, use:
        'element': None,  # Nested strategy config for all elements
        'min_size': 0,  # Minimum tuple length (variable-length only)
        'max_size': 5,  # Maximum tuple length (variable-length only)
    },

    'optional': {
        'type': 'optional',
        'element': None,  # Nested strategy config (will allow None or this type)
    },

    'union': {
        'type': 'union',
        'options': None,  # List of strategy configs (will generate one of these types)
    },

    'from_type': {
        'type': 'from_type',
        'target': None,  # Full class path (e.g., "numpy.ndarray", "a1.Point")
        # Hypothesis will use st.from_type() to automatically infer the strategy
        # Useful for custom classes, numpy arrays, pandas DataFrames, etc.
    },

    'any': {
        'type': 'any',
        # Generates one of: int, float, str, bool
        # Uses the default ranges from StrategyConfig
    },
}




def get_template_for_type(type_obj) -> dict:
    """
    Automatically select a template based on a type annotation.

    Args:
        type_obj: The type annotation (e.g., int, List[str], custom class)

    Returns:
        Template dictionary with default values
    """
    from typing import get_origin, get_args, Union
    import inspect

    # Handle basic types - return copy of template
    if type_obj == int:
        return STRATEGY_TEMPLATES['int'].copy()
    elif type_obj == float:
        return STRATEGY_TEMPLATES['float'].copy()
    elif type_obj == str:
        return STRATEGY_TEMPLATES['str'].copy()
    elif type_obj == bool:
        return STRATEGY_TEMPLATES['bool'].copy()
    elif type_obj == bytes:
        return STRATEGY_TEMPLATES['bytes'].copy()

    # Handle typing module types
    origin = get_origin(type_obj)
    args = get_args(type_obj)

    if origin in (list, type(list)) or type_obj == list:
        from typing import List
        if origin in (list, List):
            elem_type = args[0] if args else int
        else:
            elem_type = int
        return {
            'type': 'list',
            'element': get_template_for_type(elem_type),
            'min_size': 0,
            'max_size': 10
        }
    elif origin in (dict, type(dict)) or type_obj == dict:
        from typing import Dict
        if origin in (dict, Dict):
            key_type = args[0] if args else int
            val_type = args[1] if len(args) > 1 else int
        else:
            key_type = int
            val_type = int
        return {
            'type': 'dict',
            'keys': get_template_for_type(key_type),
            'values': get_template_for_type(val_type),
            'min_size': 0,
            'max_size': 10
        }
    elif origin in (set, type(set)) or type_obj == set:
        from typing import Set
        if origin in (set, Set):
            elem_type = args[0] if args else int
        else:
            elem_type = int
        return {
            'type': 'set',
            'element': get_template_for_type(elem_type),
            'min_size': 0,
            'max_size': 10
        }
    elif origin in (tuple, type(tuple)) or type_obj == tuple:
        from typing import Tuple
        if origin in (tuple, Tuple):
            if args and args[-1] is not ...:
                # Fixed-length tuple
                return {
                    'type': 'tuple',
                    'elements': [get_template_for_type(a) for a in args]
                }
            else:
                # Variable-length tuple
                elem_type = args[0] if args else int
                return {
                    'type': 'tuple',
                    'element': get_template_for_type(elem_type),
                    'min_size': 0,
                    'max_size': 5
                }
        else:
            return {
                'type': 'tuple',
                'element': get_template_for_type(int),
                'min_size': 0,
                'max_size': 5
            }
    elif origin is Union:
        # Handle Optional and Union types
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1 and len(args) == 2:
            # Optional type
            return {
                'type': 'optional',
                'element': get_template_for_type(non_none[0])
            }
        else:
            return {
                'type': 'union',
                'options': [get_template_for_type(a) for a in non_none]
            }

    # Handle custom classes using st.from_type (like the original simple logic)
    # This lets Hypothesis automatically infer the strategy
    if inspect.isclass(type_obj):
        return {
            'type': 'from_type',
            'target': f"{type_obj.__module__}.{type_obj.__name__}"
        }

    # Fallback for unknown types
    return {'type': 'any'}


def build_strategy_from_config(config: dict, param_name: str):
    """
    Automatically build a Hypothesis strategy from a configuration dictionary.

    This function uses STRATEGY_BUILDERS mapping to automatically select the right
    builder and passes all config arguments (except 'type') to it.

    Args:
        config: Configuration dictionary with 'type' and other parameters
        param_name: Name of the parameter (for nested strategies)

    Returns:
        Hypothesis SearchStrategy
    """
    strategy_type = config.get('type', 'any')

    # Handle special cases that need recursive building
    if strategy_type == 'list':
        element_config = config.get('element', {'type': 'int'})
        element_strategy = build_strategy_from_config(element_config, f"{param_name}_elem")
        kwargs = {k: v for k, v in config.items() if k not in ('type', 'element')}
        return st.lists(element_strategy, **kwargs)

    elif strategy_type == 'dict':
        key_config = config.get('keys', {'type': 'int'})
        val_config = config.get('values', {'type': 'int'})
        key_strategy = build_strategy_from_config(key_config, f"{param_name}_key")
        val_strategy = build_strategy_from_config(val_config, f"{param_name}_val")
        kwargs = {k: v for k, v in config.items() if k not in ('type', 'keys', 'values')}
        return st.dictionaries(key_strategy, val_strategy, **kwargs)

    elif strategy_type == 'set':
        element_config = config.get('element', {'type': 'int'})
        element_strategy = build_strategy_from_config(element_config, f"{param_name}_elem")
        kwargs = {k: v for k, v in config.items() if k not in ('type', 'element')}
        return st.sets(element_strategy, **kwargs)

    elif strategy_type == 'tuple':
        if 'elements' in config:
            # Fixed-length tuple
            element_strategies = [
                build_strategy_from_config(elem_config, f"{param_name}_elem{i}")
                for i, elem_config in enumerate(config['elements'])
            ]
            return st.tuples(*element_strategies)
        else:
            # Variable-length tuple
            element_config = config.get('element', {'type': 'int'})
            element_strategy = build_strategy_from_config(element_config, f"{param_name}_elem")
            kwargs = {k: v for k, v in config.items() if k not in ('type', 'element')}
            return st.lists(element_strategy, **kwargs).map(tuple)

    elif strategy_type == 'optional':
        element_config = config.get('element', {'type': 'int'})
        element_strategy = build_strategy_from_config(element_config, param_name)
        return st.none() | element_strategy

    elif strategy_type == 'union':
        options = config.get('options', [])
        if options:
            strategies = [
                build_strategy_from_config(opt_config, f"{param_name}_opt{i}")
                for i, opt_config in enumerate(options)
            ]
            return st.one_of(*strategies)
        # Fallback to any
        return st.one_of(st.integers(), st.floats(), st.text(), st.booleans())

    elif strategy_type == 'from_type':
        # Use Hypothesis's st.from_type() for automatic strategy inference
        target_path = config.get('target', '')

        try:
            # Import the target class/type
            module_name, class_name = target_path.rsplit('.', 1)
            import importlib
            module = importlib.import_module(module_name)
            target_type = getattr(module, class_name)

            # Let Hypothesis infer the strategy automatically
            return st.from_type(target_type)
        except Exception:
            # Fallback to any
            return st.one_of(st.integers(), st.floats(), st.text(), st.booleans())

    elif strategy_type == 'any':
        return st.one_of(st.integers(), st.floats(), st.text(), st.booleans())

    # For basic types, use the builder mapping
    builder = STRATEGY_BUILDERS.get(strategy_type)
    if builder:
        # Remove 'type' key and pass all other arguments to the builder
        kwargs = {k: v for k, v in config.items() if k != 'type'}
        try:
            return builder(**kwargs)
        except Exception:
            # If building fails, fallback to any
            return st.one_of(st.integers(), st.floats(), st.text(), st.booleans())

    # Unknown type, fallback to any
    return st.one_of(st.integers(), st.floats(), st.text(), st.booleans())
