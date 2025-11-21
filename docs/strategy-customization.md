# Strategy Customization Guide

This guide explains how to customize the generated strategy JSON files to control test input generation.

## Overview

When PyDiffer runs, it automatically generates a strategy JSON file that defines how test inputs are created. You can edit this file to:

- Adjust value ranges (min/max for integers, floats)
- Change collection sizes (list lengths, dictionary sizes)
- Specify custom element types
- Configure instance generation for class methods

## Strategy JSON Format

### Basic Structure

```json
{
  "_comment": "Edit this file to customize test input generation...",
  "parameters": {
    "param_name": {
      "type": "strategy_type",
      // ... strategy-specific options
    }
  }
}
```

### Class Method Structure

For class methods, an additional `instance` section is included:

```json
{
  "_comment": "...",
  "parameters": {
    "x": { "type": "integers", "min_value": -50, "max_value": 50 }
  },
  "instance": {
    "strategy": {
      "type": "builds",
      "target": "Calculator",
      "initial_value": { "type": "integers", "min_value": 0, "max_value": 100 }
    },
    "num_instances": 14
  }
}
```

---

## Common Strategy Types

### integers

Generate integer values within a range.

```json
{
  "type": "integers",
  "min_value": -100,
  "max_value": 100
}
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `min_value` | int | -50 | Minimum integer value |
| `max_value` | int | 50 | Maximum integer value |

### floats

Generate floating-point values.

```json
{
  "type": "floats",
  "min_value": -10.0,
  "max_value": 10.0,
  "allow_nan": false,
  "allow_infinity": false
}
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `min_value` | float | -50.0 | Minimum float value |
| `max_value` | float | 50.0 | Maximum float value |
| `allow_nan` | bool | false | Allow NaN values |
| `allow_infinity` | bool | false | Allow infinite values |

### text

Generate string values.

```json
{
  "type": "text",
  "min_size": 0,
  "max_size": 20
}
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `min_size` | int | 0 | Minimum string length |
| `max_size` | int | 10 | Maximum string length |
| `alphabet` | str | (all unicode) | Characters to use |

### booleans

Generate boolean values.

```json
{
  "type": "booleans"
}
```

No additional options.

---

## Collection Types

### lists

Generate list values.

```json
{
  "type": "lists",
  "elements": {
    "type": "integers",
    "min_value": 0,
    "max_value": 100
  },
  "min_size": 1,
  "max_size": 10
}
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `elements` | strategy | required | Strategy for list elements |
| `min_size` | int | 0 | Minimum list length |
| `max_size` | int | 10 | Maximum list length |
| `unique` | bool | false | Require unique elements |

### sets

Generate set values.

```json
{
  "type": "sets",
  "elements": {
    "type": "integers",
    "min_value": 1,
    "max_value": 50
  },
  "min_size": 0,
  "max_size": 5
}
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `elements` | strategy | required | Strategy for set elements |
| `min_size` | int | 0 | Minimum set size |
| `max_size` | int | 10 | Maximum set size |

### dictionaries

Generate dictionary values.

```json
{
  "type": "dictionaries",
  "keys": {
    "type": "text",
    "min_size": 1,
    "max_size": 10
  },
  "values": {
    "type": "integers",
    "min_value": 0,
    "max_value": 1000
  },
  "min_size": 0,
  "max_size": 5
}
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `keys` | strategy | required | Strategy for dictionary keys |
| `values` | strategy | required | Strategy for dictionary values |
| `min_size` | int | 0 | Minimum number of entries |
| `max_size` | int | 10 | Maximum number of entries |

### tuples

Generate tuple values with specific element types.

```json
{
  "type": "tuples",
  "element_strategies": [
    { "type": "integers", "min_value": 0, "max_value": 10 },
    { "type": "text", "max_size": 5 },
    { "type": "booleans" }
  ]
}
```

---

## Composite Types

### one_of

Generate values from one of several strategies.

```json
{
  "type": "one_of",
  "element_strategies": [
    { "type": "integers", "min_value": 0, "max_value": 100 },
    { "type": "text", "max_size": 10 },
    { "type": "none" }
  ]
}
```

### none

Generate `None` values.

```json
{
  "type": "none"
}
```

### just

Generate a specific constant value.

```json
{
  "type": "just",
  "value": 42
}
```

### sampled_from

Generate values from a specific list.

```json
{
  "type": "sampled_from",
  "elements": ["red", "green", "blue"]
}
```

---

## Custom Classes

### builds

Generate instances of custom classes.

```json
{
  "type": "builds",
  "target": "mymodule.Point",
  "x": {
    "type": "floats",
    "min_value": -100.0,
    "max_value": 100.0
  },
  "y": {
    "type": "floats",
    "min_value": -100.0,
    "max_value": 100.0
  }
}
```

| Option | Type | Description |
|--------|------|-------------|
| `target` | string | Fully qualified class name |
| `<param>` | strategy | Strategy for each constructor parameter |

### from_type

Let Hypothesis generate values for a type (useful for registered types).

```json
{
  "type": "from_type",
  "target": "numpy.ndarray"
}
```

---

## Examples

### Example 1: Testing a Sorting Function

```json
{
  "parameters": {
    "items": {
      "type": "lists",
      "elements": {
        "type": "integers",
        "min_value": -1000,
        "max_value": 1000
      },
      "min_size": 0,
      "max_size": 100
    },
    "reverse": {
      "type": "booleans"
    }
  }
}
```

### Example 2: Testing with Constrained Floats

```json
{
  "parameters": {
    "numbers": {
      "type": "lists",
      "elements": {
        "type": "floats",
        "min_value": 0.0,
        "max_value": 1.0,
        "allow_nan": false,
        "allow_infinity": false
      },
      "min_size": 2,
      "max_size": 20
    },
    "threshold": {
      "type": "floats",
      "min_value": 0.0,
      "max_value": 1.0
    }
  }
}
```

### Example 3: Testing a Calculator Class

```json
{
  "parameters": {
    "x": {
      "type": "integers",
      "min_value": -1000,
      "max_value": 1000
    },
    "y": {
      "type": "integers",
      "min_value": -1000,
      "max_value": 1000
    }
  },
  "instance": {
    "strategy": {
      "type": "builds",
      "target": "Calculator",
      "precision": {
        "type": "sampled_from",
        "elements": [2, 4, 8, 16]
      }
    },
    "num_instances": 10
  }
}
```

### Example 4: Testing with Nested Custom Types

```json
{
  "parameters": {
    "points": {
      "type": "lists",
      "elements": {
        "type": "builds",
        "target": "geometry.Point",
        "x": { "type": "floats", "min_value": -50.0, "max_value": 50.0 },
        "y": { "type": "floats", "min_value": -50.0, "max_value": 50.0 }
      },
      "min_size": 3,
      "max_size": 20
    },
    "closed": {
      "type": "booleans"
    }
  }
}
```

### Example 5: Optional Parameters

```json
{
  "parameters": {
    "name": {
      "type": "text",
      "min_size": 1,
      "max_size": 50
    },
    "age": {
      "type": "one_of",
      "element_strategies": [
        { "type": "none" },
        { "type": "integers", "min_value": 0, "max_value": 150 }
      ]
    }
  }
}
```

---

## Instance Configuration

When testing class methods, the `instance` section controls how test instances are created:

```json
{
  "instance": {
    "strategy": { /* builds strategy for the class */ },
    "num_instances": 14
  }
}
```

### num_instances

Controls how many unique instances are generated:

- **Lower values** (1-5): More tests per instance, better depth
- **Higher values** (15-20): More instance diversity, fewer tests per instance

The default is calculated using a square root heuristic based on `max_examples`.

### Customizing Instance Strategy

Edit the `strategy` section to control constructor parameters:

```json
{
  "instance": {
    "strategy": {
      "type": "builds",
      "target": "BankAccount",
      "owner": { "type": "text", "min_size": 1, "max_size": 30 },
      "initial_balance": { "type": "floats", "min_value": 0.0, "max_value": 10000.0 }
    },
    "num_instances": 20
  }
}
```

---

## Tips and Best Practices

1. **Start with defaults**: Run once without customization to see what strategies are generated

2. **Constrain ranges for edge cases**: If you want to focus on edge cases, narrow the ranges:
   ```json
   { "type": "integers", "min_value": -5, "max_value": 5 }
   ```

3. **Increase sizes for stress testing**: For performance testing, increase collection sizes:
   ```json
   { "type": "lists", "elements": {...}, "max_size": 1000 }
   ```

4. **Use `sampled_from` for enums**: For parameters with known valid values:
   ```json
   { "type": "sampled_from", "elements": ["GET", "POST", "PUT", "DELETE"] }
   ```

5. **Disable NaN/Infinity for math functions**: Avoid undefined behavior:
   ```json
   { "type": "floats", "allow_nan": false, "allow_infinity": false }
   ```

6. **Balance instance diversity**: For class methods, consider your testing goals when setting `num_instances`

---

## Hypothesis Documentation

For complete strategy documentation, see the official Hypothesis documentation:

- [Core Strategies](https://hypothesis.readthedocs.io/en/latest/data.html)
- [Strategy Reference](https://hypothesis.readthedocs.io/en/latest/reference/strategies.html)
- [builds() Documentation](https://hypothesis.readthedocs.io/en/latest/reference/strategies.html#hypothesis.strategies.builds)

---

## See Also

- [Strategy System](strategy-system.md) - Technical details of how strategies are generated
- [Type Inference](type-inference.md) - How types are discovered from code
