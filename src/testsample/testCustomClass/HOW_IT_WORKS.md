# How StrategySynthesizer Handles Custom Classes

This document traces the exact flow of how `typing.List[a1.Point]` becomes `builds(Point, x=floats(), y=floats())`.

## Input Type

From TypeDiscoverer, we get:
```python
{'points': typing.List[a1.Point], 'threshold': <class 'float'>}
```

## Step-by-Step Flow

### Step 1: _create_strategy_from_type()

**Input**: `param_type = typing.List[a1.Point]`

**Location**: [strategies.py:78-104](../src/dt/strategy/strategies.py#L78-L104)

```python
def _create_strategy_from_type(self, param_type: Any, param_name: str):
    # Handle string types from RightTyper
    if isinstance(param_type, str):
        return self._from_type_string(param_type)  # ❌ Not a string

    # Handle ready-made strategies
    if isinstance(param_type, st.SearchStrategy):
        return param_type  # ❌ Not a strategy

    # Handle keyword hints
    if param_type in ["positive_int", "string", "list", "float"]:
        return self._normalize_hint(param_type)  # ❌ Not a keyword

    # Handle type annotations ✅
    return self._from_annotation(param_type)  # Go here!
```

Since `typing.List[a1.Point]` is a type annotation, it goes to `_from_annotation()`.

---

### Step 2: _from_annotation() - Parse List

**Input**: `annotation = typing.List[a1.Point]`

**Location**: [strategies.py:214-237](../src/dt/strategy/strategies.py#L214-L237)

```python
def _from_annotation(self, annotation: Any):
    # Direct hits - check registry
    if annotation in self.registry:
        return self.registry[annotation]()  # ❌ List[Point] not in registry

    # Get origin and args
    origin = get_origin(annotation)  # ✅ origin = list
    args = get_args(annotation)      # ✅ args = (a1.Point,)

    # Containers - List handling
    if origin in (list, List):  # ✅ Match!
        elem_ann = args[0] if args else Any  # ✅ elem_ann = a1.Point

        # Recursively process the element type
        elem = self._from_annotation(elem_ann)  # 🔄 Recurse with a1.Point

        return st.lists(elem, max_size=self.config.LIST_MAX_SIZE)
```

**Key insight**:
- `get_origin(typing.List[a1.Point])` → `list`
- `get_args(typing.List[a1.Point])` → `(a1.Point,)` (a tuple containing the Point class)

Now it recursively calls `_from_annotation(a1.Point)` to generate a strategy for the element type.

---

### Step 3: _from_annotation() - Handle Point Class (RECURSIVE CALL)

**Input**: `annotation = a1.Point` (the actual Point class object)

**Location**: [strategies.py:214-296](../src/dt/strategy/strategies.py#L214-L296)

```python
def _from_annotation(self, annotation: Any):
    # Direct hits - check registry
    if annotation in self.registry:
        return self.registry[annotation]()  # ❌ Point not in registry

    # Handle typing.Any
    if annotation is Any:
        return self.registry[Any]()  # ❌ Not Any

    # Get origin and args
    origin = get_origin(annotation)  # ✅ origin = None (Point is a regular class)
    args = get_args(annotation)      # ✅ args = ()

    # Not a container... skip to end

    # Last-ditch: try Hypothesis' type-based strategy ✅
    try:
        return st.from_type(annotation)  # 🎯 Use Hypothesis's st.from_type(Point)!
    except Exception:
        # Fallback
        return st.one_of(...)
```

**Key insight**: When the annotation is a regular class like `Point`, Hypothesis's `st.from_type()` is called.

---

### Step 4: Hypothesis st.from_type() - Magic Happens!

**Input**: `Point` class

Hypothesis's `st.from_type()` inspects the `Point` class:

```python
class Point:
    def __init__(self, x: float, y: float):  # ✅ Has type annotations!
        self.x = x
        self.y = y
```

Hypothesis sees:
1. `Point.__init__` has parameters `x: float` and `y: float`
2. It automatically creates: `builds(Point, x=floats(), y=floats())`

This is Hypothesis's built-in capability! It uses:
- **Introspection**: Inspects `__init__` signature
- **Annotation parsing**: Reads `x: float, y: float`
- **Strategy generation**: Maps `float` → `st.floats()`
- **Builder pattern**: Uses `st.builds()` to construct instances

---

### Step 5: Back to List Processing

Now the recursive call returns with the Point strategy:

```python
# Back in Step 2
elem = self._from_annotation(a1.Point)
# ✅ elem = builds(Point, x=floats(), y=floats())

return st.lists(elem, max_size=self.config.LIST_MAX_SIZE)
# ✅ Returns: lists(builds(Point, x=floats(), y=floats()), max_size=10)
```

---

## Complete Flow Diagram

```
Input: typing.List[a1.Point]
    │
    ▼
_create_strategy_from_type()
    │
    ├─ Not a string
    ├─ Not a SearchStrategy
    ├─ Not a keyword hint
    │
    └─► _from_annotation(typing.List[a1.Point])
            │
            ├─ Not in registry
            ├─ get_origin() → list ✅
            ├─ get_args() → (a1.Point,) ✅
            │
            ├─ origin in (list, List) → TRUE
            │
            └─► elem = _from_annotation(a1.Point)  [RECURSIVE]
                    │
                    ├─ Not in registry
                    ├─ get_origin() → None
                    │
                    └─► st.from_type(Point)  [HYPOTHESIS]
                            │
                            ├─ Inspect Point.__init__
                            ├─ Find: x: float, y: float
                            │
                            └─► builds(Point, x=floats(), y=floats()) ✅
                    │
                    ◄── Returns strategy for Point
            │
            └─► st.lists(builds(Point, ...), max_size=10) ✅
    │
    ◄── Returns final strategy

Output: lists(builds(Point, x=floats(), y=floats()), max_size=10)
```

---

## Key Components

### 1. Python's typing module

```python
from typing import get_origin, get_args

origin = get_origin(typing.List[Point])  # → list
args = get_args(typing.List[Point])      # → (Point,)
```

### 2. Hypothesis's st.from_type()

Hypothesis has built-in support for creating strategies from type hints. When given a class:

```python
st.from_type(Point)
```

It automatically:
1. Inspects `Point.__init__(self, x: float, y: float)`
2. Generates strategies for each parameter: `x` → `floats()`, `y` → `floats()`
3. Returns `builds(Point, x=floats(), y=floats())`

### 3. Recursive Type Processing

The code handles nested types recursively:
- `List[Point]` → process `List`, then recursively process `Point`
- `List[List[Point]]` → would work the same way, recursing twice
- `Dict[str, List[Point]]` → would recursively process both key and value types

---

## Why Type Annotations Are Critical

Without type annotations on `Point.__init__`, Hypothesis would fail:

```python
# ❌ Without annotations - Hypothesis can't infer types
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

# ✅ With annotations - Hypothesis knows what to generate
class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
```

---

## Summary

The flow is:
1. **TypeDiscoverer** provides `typing.List[a1.Point]`
2. **StrategySynthesizer** uses `get_origin()`/`get_args()` to decompose it
3. **Recursion** handles the `List` container and `Point` element separately
4. **Hypothesis st.from_type()** does the heavy lifting for custom classes
5. **Result**: `lists(builds(Point, x=floats(), y=floats()))`

The magic is that Hypothesis's `st.from_type()` can automatically generate strategies for any class with properly type-annotated `__init__` methods!
