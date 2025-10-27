# Example Test Output

## Command
### a1 b1, having a custom defined type Point, both have type annotation
```bash
python run_ab.py \
  --a testsample/testCustomClass/a1.py \
  --b testsample/testCustomClass/b1.py \
  --func find_closest_points \
  --max-examples 50 \
  --log VERBOSE
```
### a2 b2, having a custom defined type Point, both DO NOT have type annotation
```bash
python run_ab.py \
  --a testsample/testCustomClass/a2.py \
  --b testsample/testCustomClass/b2.py \
  --func find_closest_points \
  --test testsample/testCustomClass/test_a2.py \
  --max-examples 50 \
  --log VERBOSE
```
### a3 b3, using numpy as input, both have type annotation
```bash
python run_ab.py \
  --a testsample/testCustomClass/a3.py \
  --b testsample/testCustomClass/b3.py \
  --func zscore \
  --max-examples 50 \
  --log VERBOSE
```
### a4 b4, using numpy as input, both DO NOT have type annotation
```bash
python run_ab.py \
  --a testsample/testCustomClass/a4.py \
  --b testsample/testCustomClass/b4.py \
  --func zscore \
  --test testsample/testCustomClass/test_a4.py \
  --max-examples 50 \
  --log VERBOSE
```

## Output

```
[TypeDiscoverer] Found annotation for 'points': typing.List[a1.Point]
[TypeDiscoverer] Found annotation for 'threshold': <class 'float'>
[TypeDiscoverer] Type discovered as {'points': typing.List[a1.Point], 'threshold': <class 'float'>}

✅ Test Strategies Successfully Generated:
StrategyPlan(arg_strategy=tuples(
    lists(builds(Point, x=floats(), y=floats()), max_size=10),
    floats(min_value=-50.0, max_value=50.0, allow_nan=False, allow_infinity=False)
))

[ABRunner] Executing Tests
[ABComparator] Comparing Results

find_closest_points(testCustomClass/a1.py vs testCustomClass/b1.py): no difference found
Summary: total=50, successes=50, mismatches=0
```

## Explanation

### Type Discovery Phase

The framework discovers the function signature:
```python
def find_closest_points(points: List[Point], threshold: float) -> List[tuple[Point, Point]]
```

It identifies:
- Parameter `points`: `typing.List[a1.Point]` - a custom class!
- Parameter `threshold`: `float` - a built-in type

### Strategy Generation Phase

The framework generates a Hypothesis strategy:

```python
tuples(
    # First argument: List of Point objects
    lists(
        builds(Point, x=floats(), y=floats()),  # Build Point instances
        max_size=10
    ),
    # Second argument: float threshold
    floats(min_value=-50.0, max_value=50.0, allow_nan=False, allow_infinity=False)
)
```

This strategy will generate test cases like:
- `([Point(1.5, 2.3), Point(-3.2, 4.1)], 5.0)`
- `([Point(0, 0), Point(1, 1), Point(2, 2)], 2.5)`
- `([], 10.0)` - edge case: empty list
- etc.

### Execution Phase

The framework:
1. Generates 50 random test inputs using the strategy
2. Runs `a1.find_closest_points()` with each input
3. Runs `b1.find_closest_points()` with the same input
4. Compares the results

### Results

All 50 test cases passed with identical results, confirming that the two implementations are functionally equivalent despite their different coding styles.

## Key Insights

1. **Custom classes work seamlessly**: The `Point` class is automatically handled
2. **Type annotations are crucial**: The framework uses `List[Point]` to generate proper test data
3. **Hypothesis builds complex objects**: `builds(Point, x=floats(), y=floats())` creates Point instances
4. **Property-based testing**: Instead of manual test cases, the framework explores the input space automatically
