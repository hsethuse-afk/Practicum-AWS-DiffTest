# Custom Class Differential Testing Example

This directory contains test files demonstrating differential testing with custom classes.

## Files

- **a1.py**: Implementation A with a custom `Point` class
- **b1.py**: Implementation B with the same `Point` class but non-functional changes
- **README.md**: This file

## Custom Class: Point

Both files define a `Point` class representing a point in 2D space:

```python
class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def distance_to(self, other: 'Point') -> float:
        """Calculate Euclidean distance to another point."""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
```

## Functions to Test

### 1. find_closest_points(points: List[Point], threshold: float)

Finds all pairs of points that are closer than the threshold distance.

**Implementation Differences** (non-functional):
- **A**: Uses nested `range()` loops with indices
- **B**: Uses `enumerate()` and list slicing

### 2. calculate_centroid(points: List[Point])

Calculates the center point (centroid) of a list of points.

**Implementation Differences** (non-functional):
- **A**: Uses explicit loop accumulation
- **B**: Uses `sum()` with generator expressions

## Running Tests

### Test find_closest_points

```bash
python src/run_ab.py \
  --a testCustomClass/a1.py \
  --b testCustomClass/b1.py \
  --func find_closest_points \
  --max-examples 100
```

### Test calculate_centroid

```bash
python src/run_ab.py \
  --a testCustomClass/a1.py \
  --b testCustomClass/b1.py \
  --func calculate_centroid \
  --max-examples 100
```

### With Verbose Logging

```bash
python src/run_ab.py \
  --a testCustomClass/a1.py \
  --b testCustomClass/b1.py \
  --func find_closest_points \
  --max-examples 100 \
  --log VERBOSE
```

## How It Works

### Type Discovery

The differential testing framework automatically discovers that the function uses a custom `Point` class:

1. **Type Annotation Detection**: Reads `List[Point]` from function signatures
2. **Type Resolution**: Resolves `Point` to the actual class from the module
3. **Strategy Generation**: Uses Hypothesis's `builds()` to construct `Point` objects

### Strategy Generation

For `find_closest_points(points: List[Point], threshold: float)`, the framework generates:

```python
tuples(
    lists(builds(Point, x=floats(), y=floats()), max_size=10),
    floats(min_value=-50.0, max_value=50.0)
)
```

This generates:
- Lists of `Point` objects with random `x` and `y` coordinates
- Random float thresholds between -50 and 50

### Differential Testing

The framework then:
1. Generates test inputs using the strategy
2. Runs both implementations (a1.py and b1.py) with the same inputs
3. Compares the outputs
4. Reports any differences

## Expected Results

Since a1.py and b1.py are functionally equivalent (only stylistic differences), you should see:

```
✅ Test Strategies Successfully Generated
[ABRunner] Executing Tests
[ABComparator] Comparing Results
find_closest_points(testCustomClass/a1.py vs testCustomClass/b1.py): no difference found
Summary: total=100, successes=100, mismatches=0
```

## Key Features Demonstrated

1. ✅ **Custom class support**: The framework handles user-defined classes
2. ✅ **Type annotation parsing**: Correctly interprets `List[Point]` annotations
3. ✅ **Automatic strategy generation**: Uses `builds()` to construct custom objects
4. ✅ **Property-based testing**: Generates diverse test cases automatically
5. ✅ **Differential testing**: Compares two implementations for equivalence

## Notes

- Both files must define the `Point` class identically for proper comparison
- The `Point` class includes `__eq__()` for equality comparison
- The `Point` class includes `__repr__()` for readable output in diffs
