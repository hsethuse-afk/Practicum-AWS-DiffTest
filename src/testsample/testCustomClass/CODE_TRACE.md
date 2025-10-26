# Code Trace: From typing.List[Point] to builds(Point, ...)

This document shows the exact code execution path with line numbers.

## Input

```python
param_types = {'points': typing.List[a1.Point], 'threshold': <class 'float'>}
```

## Execution Trace

### Entry Point: StrategySynthesizer.create_strategy()

**File**: [strategies.py:40-76](../src/dt/strategy/strategies.py#L40-L76)

```python
def create_strategy(self, func, param_hints=None, test_file=None):
    # ... discover param_types ...

    # Line 64-70: For each parameter, create strategy
    for param in sig.parameters.values():
        param_type = param_types.get(param.name, Any)  # 'points' → List[a1.Point]
        strategy = self._create_strategy_from_type(param_type, param.name)
        strategies.append(strategy)
```

**Call Stack**:
```
_create_strategy_from_type(typing.List[a1.Point], 'points')
```

---

### Level 1: _create_strategy_from_type()

**File**: [strategies.py:78-104](../src/dt/strategy/strategies.py#L78-L104)

```python
def _create_strategy_from_type(self, param_type: Any, param_name: str):
    # Line 92-93: Check if string
    if isinstance(param_type, str):
        return self._from_type_string(param_type)  # ❌ Skip - not a string

    # Line 96-97: Check if already a strategy
    if isinstance(param_type, st.SearchStrategy):
        return param_type  # ❌ Skip - not a strategy

    # Line 100-101: Check if keyword hint
    if param_type in ["positive_int", "string", "list", "float"]:
        return self._normalize_hint(param_type)  # ❌ Skip - not a keyword

    # Line 104: Default - handle as type annotation
    return self._from_annotation(param_type)  # ✅ Go here!
```

**Call Stack**:
```
_from_annotation(typing.List[a1.Point])
```

---

### Level 2: _from_annotation() - First Call (List)

**File**: [strategies.py:214-237](../src/dt/strategy/strategies.py#L214-L237)

```python
def _from_annotation(self, annotation: Any):
    # Line 216-217: Check registry
    if annotation in self.registry:
        return self.registry[annotation]()  # ❌ Skip - List[Point] not in registry

    # Line 220-221: Check for Any
    if annotation is Any:
        return self.registry[Any]()  # ❌ Skip - not Any

    # Line 223-224: Decompose type annotation
    origin = get_origin(annotation)  # origin = list
    args = get_args(annotation)      # args = (a1.Point,)

    # Line 231-237: Handle List type
    if origin in (list, List):  # ✅ Match!
        # Line 233: Get element type
        elem_ann = args[0] if args else Any  # elem_ann = a1.Point

        # Line 234-236: Recursively create strategy for element type
        elem = self._from_annotation(elem_ann)  # 🔄 RECURSIVE CALL

        # Line 237: Wrap in lists()
        return st.lists(elem, max_size=self.config.LIST_MAX_SIZE)
```

**Call Stack**:
```
_from_annotation(a1.Point)  [RECURSIVE]
```

---

### Level 3: _from_annotation() - Second Call (Point)

**File**: [strategies.py:214-296](../src/dt/strategy/strategies.py#L214-L296)

```python
def _from_annotation(self, annotation: Any):
    # annotation = a1.Point (the actual class)

    # Line 216-217: Check registry
    if annotation in self.registry:
        return self.registry[annotation]()  # ❌ Skip - Point not in registry

    # Line 220-221: Check for Any
    if annotation is Any:
        return self.registry[Any]()  # ❌ Skip - not Any

    # Line 223-224: Decompose type annotation
    origin = get_origin(annotation)  # origin = None (Point is a class, not generic)
    args = get_args(annotation)      # args = ()

    # Line 231: Check if list
    if origin in (list, List):  # ❌ Skip - origin is None

    # Line 239: Check if set
    if origin in (set, Set):  # ❌ Skip - origin is None

    # Line 246: Check if tuple
    if origin in (tuple, Tuple):  # ❌ Skip - origin is None

    # Line 266: Check if dict
    if origin in (dict, Dict):  # ❌ Skip - origin is None

    # Line 281: Check if Union
    if origin is Union:  # ❌ Skip - origin is None

    # Line 287-290: Last resort - use Hypothesis st.from_type()
    try:
        return st.from_type(annotation)  # ✅ Call Hypothesis!
    except Exception:
        return st.one_of(...)  # Fallback (not reached in this case)
```

**Call Stack**:
```
hypothesis.strategies.from_type(a1.Point)  [HYPOTHESIS LIBRARY]
```

---

### Level 4: Hypothesis st.from_type() - Internal

**Library**: Hypothesis (external library)

Hypothesis's `st.from_type()` performs:

1. **Inspect the class**:
   ```python
   import inspect
   sig = inspect.signature(Point.__init__)
   # sig = (self, x: float, y: float)
   ```

2. **Extract parameter annotations**:
   ```python
   params = sig.parameters
   # {'self': ..., 'x': Parameter(annotation=float), 'y': Parameter(annotation=float)}
   ```

3. **Generate strategies for each parameter**:
   ```python
   x_strategy = st.floats()  # for x: float
   y_strategy = st.floats()  # for y: float
   ```

4. **Build the constructor strategy**:
   ```python
   return st.builds(Point, x=st.floats(), y=st.floats())
   ```

**Returns**: `builds(Point, x=floats(), y=floats())`

---

### Return Path: Unwinding the Stack

Now the recursive calls return in reverse order:

#### Level 3 → Level 2 (Point strategy returned)

```python
# Back in _from_annotation() for List[Point]
elem = self._from_annotation(a1.Point)
# elem = builds(Point, x=floats(), y=floats())  ✅ Received

return st.lists(elem, max_size=self.config.LIST_MAX_SIZE)
# Returns: lists(builds(Point, x=floats(), y=floats()), max_size=10)  ✅
```

#### Level 2 → Level 1 (List strategy returned)

```python
# Back in _create_strategy_from_type()
return self._from_annotation(param_type)
# Returns: lists(builds(Point, x=floats(), y=floats()), max_size=10)  ✅
```

#### Level 1 → Entry Point (Strategy added to list)

```python
# Back in create_strategy()
for param in sig.parameters.values():
    strategy = self._create_strategy_from_type(param_type, param.name)
    strategies.append(strategy)
    # strategies = [lists(builds(Point, ...), max_size=10)]
```

---

## Final Result

```python
StrategyPlan(
    arg_strategy=tuples(
        lists(builds(Point, x=floats(), y=floats()), max_size=10),  # for 'points'
        floats(min_value=-50.0, max_value=50.0)                     # for 'threshold'
    )
)
```

---

## Key Functions Used

### Python Standard Library
- `typing.get_origin()` - Extracts `list` from `List[Point]`
- `typing.get_args()` - Extracts `(Point,)` from `List[Point]`
- `inspect.signature()` - Gets function/method signatures (used by Hypothesis)

### Hypothesis Library
- `st.from_type()` - Automatically generates strategies for classes
- `st.builds()` - Creates instances by calling constructors
- `st.lists()` - Generates lists with element strategies
- `st.floats()` - Generates floating-point numbers

---

## Call Graph

```
create_strategy()
    │
    └─► _create_strategy_from_type(List[Point], 'points')
            │
            └─► _from_annotation(List[Point])
                    │
                    ├─ get_origin() → list
                    ├─ get_args() → (Point,)
                    │
                    └─► _from_annotation(Point)  [RECURSIVE]
                            │
                            └─► st.from_type(Point)  [HYPOTHESIS]
                                    │
                                    ├─ inspect.signature(Point.__init__)
                                    ├─ Extract: x: float, y: float
                                    │
                                    └─► builds(Point, x=floats(), y=floats())
                            │
                            ◄── returns Point strategy
                    │
                    └─► st.lists(Point_strategy, max_size=10)
                    │
                    ◄── returns List[Point] strategy
            │
            ◄── returns final strategy
    │
    └─► Combine with threshold strategy
    │
    └─► Return StrategyPlan(tuples(...))
```

---

## Summary

The entire process relies on:
1. **Recursive decomposition** of nested types
2. **Python's typing introspection** (`get_origin`, `get_args`)
3. **Hypothesis's automatic inference** from type annotations
4. **Proper type annotations** on the `Point` class

Without any of these pieces, the automatic strategy generation would fail!
