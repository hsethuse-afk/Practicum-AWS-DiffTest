# Strategy Configuration Guide

This guide explains how to customize the default values used for generating test inputs in the differential testing framework.

## Overview

The `StrategyConfig` class in [strategy_config.py](strategy_config.py) defines all default values used by Hypothesis to generate test data. You can customize these values to control:

- The range of integers and floats generated
- The maximum size of strings and containers
- Behavior of special type hints

## Configuration Options

### Basic Type Configurations

```python
# Integer strategy
INT_MIN_VALUE = -50        # Minimum integer value
INT_MAX_VALUE = 50         # Maximum integer value

# Float strategy
FLOAT_MIN_VALUE = -50.0    # Minimum float value
FLOAT_MAX_VALUE = 50.0     # Maximum float value
FLOAT_ALLOW_NAN = False    # Allow NaN values
FLOAT_ALLOW_INFINITY = False  # Allow infinity values

# String strategy
STRING_MAX_SIZE = 10       # Maximum string length
```

### Container Configurations

```python
LIST_MAX_SIZE = 10         # Maximum list size
SET_MAX_SIZE = 10          # Maximum set size
DICT_MAX_SIZE = 10         # Maximum dictionary size
TUPLE_MAX_SIZE = 5         # Maximum tuple size (for variable-length tuples)
```

### Keyword Hint Configurations

```python
POSITIVE_INT_MIN = 1       # Minimum for "positive_int" hint
POSITIVE_INT_MAX = 100     # Maximum for "positive_int" hint
KEYWORD_STRING_MAX_SIZE = 20  # String size for "string" hint
KEYWORD_FLOAT_MIN = -100.0    # Float min for "float" hint
KEYWORD_FLOAT_MAX = 100.0     # Float max for "float" hint
```

## How to Customize

### Method 1: Edit the Configuration File (Simple)

Directly edit the values in [strategy_config.py](strategy_config.py):

```python
class StrategyConfig:
    # Change these values to your needs
    INT_MIN_VALUE = -1000  # Changed from -50
    INT_MAX_VALUE = 1000   # Changed from 50
    STRING_MAX_SIZE = 50   # Changed from 10
    # ... etc
```

**Pros:** Simple, affects all uses of the framework
**Cons:** Changes affect everyone using the codebase

### Method 2: Create a Custom Config Class (Recommended)

Create your own config class that inherits from `StrategyConfig`:

```python
from dt.strategy_config import StrategyConfig
from dt.strategies import StrategySynthesizer
from dt.orchestrator import Orchestrator

# Define custom configuration
class MyCustomConfig(StrategyConfig):
    INT_MIN_VALUE = -1000
    INT_MAX_VALUE = 1000
    STRING_MAX_SIZE = 50
    LIST_MAX_SIZE = 20

# Use it in your orchestrator
class CustomOrchestrator(Orchestrator):
    def __init__(self, log_mode=2):
        super().__init__(log_mode)
        # Replace the strategy synthesizer with one using custom config
        self.strategy = StrategySynthesizer(config=MyCustomConfig)
```

**Pros:** Doesn't modify shared code, isolated to your use case
**Cons:** Requires more code

### Method 3: Per-Test Customization

You can create different configs for different test scenarios:

```python
from dt.strategy_config import StrategyConfig

class SmallInputConfig(StrategyConfig):
    """Use smaller inputs for faster tests"""
    INT_MIN_VALUE = -10
    INT_MAX_VALUE = 10
    LIST_MAX_SIZE = 5
    STRING_MAX_SIZE = 5

class LargeInputConfig(StrategyConfig):
    """Use larger inputs for stress testing"""
    INT_MIN_VALUE = -10000
    INT_MAX_VALUE = 10000
    LIST_MAX_SIZE = 100
    STRING_MAX_SIZE = 100

# Use different configs for different tests
quick_test = StrategySynthesizer(config=SmallInputConfig)
stress_test = StrategySynthesizer(config=LargeInputConfig)
```

## Examples

### Example 1: Testing with Larger Integers

```python
class BigIntConfig(StrategyConfig):
    INT_MIN_VALUE = -1000000
    INT_MAX_VALUE = 1000000

# Use in orchestrator
orchestrator = Orchestrator()
orchestrator.strategy = StrategySynthesizer(config=BigIntConfig)
```

### Example 2: Testing with Edge Cases

```python
class EdgeCaseConfig(StrategyConfig):
    FLOAT_ALLOW_NAN = True         # Include NaN in tests
    FLOAT_ALLOW_INFINITY = True    # Include infinity in tests
    INT_MIN_VALUE = -2**31         # Test 32-bit integer limits
    INT_MAX_VALUE = 2**31 - 1
```

### Example 3: Performance Testing Config

```python
class PerformanceConfig(StrategyConfig):
    """Large inputs for performance testing"""
    LIST_MAX_SIZE = 1000
    STRING_MAX_SIZE = 1000
    DICT_MAX_SIZE = 500
```

## Configuration Impact

Changing these values affects:

1. **Test Coverage**: Larger ranges = more diverse inputs
2. **Test Speed**: Larger sizes = slower tests
3. **Bug Detection**: Different ranges may expose different bugs

## Best Practices

1. **Start Small**: Begin with small ranges and increase as needed
2. **Match Your Domain**: If your function handles 0-100, configure `INT_MIN_VALUE = 0, INT_MAX_VALUE = 100`
3. **Consider Performance**: Large containers can slow down tests significantly
4. **Test Edge Cases**: Use configs that test boundary conditions
5. **Document Custom Configs**: Add comments explaining why you chose specific values

## Troubleshooting

### Tests are too slow
- Reduce `LIST_MAX_SIZE`, `DICT_MAX_SIZE`, `SET_MAX_SIZE`
- Reduce `STRING_MAX_SIZE`
- Narrow the range of `INT_MIN_VALUE`/`INT_MAX_VALUE`

### Not finding bugs
- Increase container sizes
- Widen integer/float ranges
- Enable `FLOAT_ALLOW_NAN` and `FLOAT_ALLOW_INFINITY`
- Use edge case values (0, -1, max int, etc.)

### Tests are inconsistent
- Make sure both implementations use the same config
- Check if you're using different configs in different test runs

## See Also

- [strategies.py](strategies.py) - The StrategySynthesizer implementation
- [Hypothesis documentation](https://hypothesis.readthedocs.io/) - Learn more about Hypothesis strategies
