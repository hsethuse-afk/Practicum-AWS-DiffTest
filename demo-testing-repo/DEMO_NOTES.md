# Demo Testing Repository - Overview

## Purpose
This repository serves as a controlled testing environment for demonstrating differential testing capabilities with property-based testing using Hypothesis.

## Key Features for Demo

### 1. No Type Annotations ✓
- All Python files lack type hints
- Perfect for showcasing type inference capabilities
- Type inference engine can use tests to infer types

### 2. Target Function: Class Method with Complex Inputs ✓
- **Location**: `taskmanager/manager.py:32-128`
- **Function**: `TaskManager.analyze_task_metrics()`
- **Current Algorithm**: Bubble sort with weighted scoring (O(n²))
- **Refactor Plan**: Change to quicksort (O(n log n)) for "after" version

### 3. Complex Multi-Type Input Parameters ✓

The target function accepts:
- **`metrics_array`**: 2D numpy array (multi-dimensional task metrics)
- **`weights`**: Optional 1D numpy array (metric weights)
- **`config`**: Custom SortConfig object (sorting configuration)
- **`exclusions`**: Dictionary container with 'indices' (list) and 'threshold' (float)

This showcases:
- ✅ Third-party library support (numpy)
- ✅ Custom defined class (SortConfig)
- ✅ Container types (dict with lists)
- ✅ Multiple parameter types (arrays, objects, dicts, floats, booleans)
- ✅ Optional parameters with defaults
- ✅ Rich input space for property-based testing

### 4. Multi-file Structure ✓
Files:
- `taskmanager/task.py` - Task model with business logic
- `taskmanager/manager.py` - Main manager with target function
- `taskmanager/storage.py` - File I/O utilities
- `taskmanager/config.py` - SortConfig class definition
- `tests/test_manager.py` - Original unit tests (12 test cases)
- `tests/test_analyze_metrics.py` - Comprehensive numpy tests (29 test cases)
- `demo_metrics.py` - Executable demo with 5 scenarios

### 5. Comprehensive Executable Tests ✓
- Run: `python tests/test_analyze_metrics.py`
- 29 test cases covering diverse scenarios:
  - Empty arrays
  - Single/multiple tasks
  - Various array dimensions (1D, 2D, large arrays)
  - Custom weights (positive, negative, zero)
  - Custom config objects (reverse order, max iterations, normalization)
  - Dictionary exclusions (indices, thresholds)
  - Threshold filtering
  - Edge cases (negatives, zeros, identical values)
  - Error handling (dimension mismatches)
  - Complex scenarios using all parameters together

## Target Function Details

### Current Implementation (Bubble Sort)

```python
def analyze_task_metrics(self, metrics_array, weights=None, config=None, exclusions=None):
    """
    Analyze and sort task indices based on multi-dimensional performance metrics.

    Uses bubble sort algorithm with weighted metric scoring.

    Args:
        metrics_array: 2D numpy array where each row represents a task's metrics
        weights: 1D numpy array of weights for each metric dimension
        config: SortConfig object containing sorting configuration
        exclusions: Dictionary with 'indices' (list) and 'threshold' (float)

    Returns:
        1D numpy array of sorted task indices based on weighted scores
    """
```

### SortConfig Class

```python
class SortConfig:
    def __init__(self, algorithm="bubble", reverse_order=False, stability_required=True):
        self.algorithm = algorithm
        self.reverse_order = reverse_order
        self.stability_required = stability_required  # Controls normalization
        self.max_iterations = 1000
```

### Input Space Characteristics

Perfect for Hypothesis property-based testing:

1. **Numpy Arrays**:
   - Dimensions: 1D to multi-dimensional arrays
   - Sizes: Empty to large (100+ elements)
   - Value ranges: Negative, zero, positive, mixed
   - Data types: Float, integer

2. **Weights**:
   - None (defaults to uniform)
   - Uniform, varying, negative, zero
   - Matching/mismatching dimensions

3. **Config Object**:
   - Various algorithm settings
   - Reverse order: True/False
   - Normalization: True/False
   - Max iterations: 1 to 10000

4. **Exclusions Dictionary**:
   - Empty dict
   - Indices list: [], [0], [0, 1, 2], etc.
   - Thresholds: 0.0 to high values

5. **Edge Cases**:
   - All parameters None (use defaults)
   - All tasks excluded
   - Identical values
   - Extreme ranges

### Suggested Refactor for "After" Version

Replace bubble sort with quicksort algorithm (keeping same interface):

```python
def analyze_task_metrics(self, metrics_array, weights=None, config=None, exclusions=None):
    """
    Analyze and sort task indices based on multi-dimensional performance metrics.

    Uses quicksort algorithm with weighted metric scoring.
    """
    # ... same preprocessing and configuration ...

    def quicksort_indices(indices, scores, low, high):
        if low < high:
            pi = partition(indices, scores, low, high)
            quicksort_indices(indices, scores, low, pi - 1)
            quicksort_indices(indices, scores, pi + 1, high)

    def partition(indices, scores, low, high):
        pivot_score = scores[indices[high]]
        i = low - 1
        for j in range(low, high):
            if config.reverse_order:
                condition = scores[indices[j]] <= pivot_score
            else:
                condition = scores[indices[j]] >= pivot_score

            if condition:
                i += 1
                indices[i], indices[j] = indices[j], indices[i]

        indices[i + 1], indices[high] = indices[high], indices[i + 1]
        return i + 1

    quicksort_indices(indices, scores, 0, len(indices) - 1)

    # ... same filtering ...
```

## Demo Talking Points

1. **Type Inference**: Show how the tool infers:
   - Numpy array types and shapes
   - Custom class structure
   - Dictionary schema with nested types

2. **Third-party Libraries**: Demonstrates handling of numpy operations

3. **Custom Classes**: SortConfig object with methods and properties

4. **Container Types**: Dictionary with mixed value types (list, float)

5. **Algorithm Change**: Highlight the sorting algorithm refactor (bubble → quicksort)

6. **Behavioral Equivalence**: Tests ensure both versions produce identical results

7. **Property-based Testing**: Rich input space with 29+ test cases covering edge cases

8. **Real-world Scenario**: Task prioritization with weighted metrics is practical

9. **Complexity Balance**: Complex enough to showcase capabilities, simple enough to be reliable

## Running the Demo

### Install Dependencies
```bash
pip install numpy
```

### Run Tests
```bash
# Original tests
python tests/test_manager.py

# Numpy-based tests (29 test cases) - TARGET FUNCTION TESTS
python tests/test_analyze_metrics.py -v
```

### Run Demo Scenarios
```bash
python demo_metrics.py
```

## Project Statistics
- Python files: 9
- Total lines: ~800
- Test cases: 41 (12 original + 29 numpy-based)
- Target function complexity: High (numpy operations, multi-dimensional sorting, custom classes)
- Third-party dependencies: numpy
- Input parameter combinations: 1000+ possible variations

## Hypothesis Testing Strategy

For property-based testing with Hypothesis, consider strategies like:

```python
from hypothesis import given, strategies as st
from hypothesis.extra.numpy import arrays
import numpy as np
from taskmanager import SortConfig

# Strategy for SortConfig objects
@st.composite
def sort_configs(draw):
    return SortConfig(
        algorithm=draw(st.sampled_from(["bubble", "quick", "merge"])),
        reverse_order=draw(st.booleans()),
        stability_required=draw(st.booleans())
    )

# Strategy for exclusions dictionaries
@st.composite
def exclusions_dicts(draw, max_indices=20):
    num_excluded = draw(st.integers(min_value=0, max_value=max_indices))
    indices = draw(st.lists(
        st.integers(min_value=0, max_value=max_indices-1),
        min_size=num_excluded,
        max_size=num_excluded,
        unique=True
    ))
    threshold = draw(st.floats(min_value=0.0, max_value=1.0))
    return {'indices': indices, 'threshold': threshold}

@given(
    metrics=arrays(
        dtype=np.float64,
        shape=st.tuples(
            st.integers(min_value=0, max_value=50),  # num tasks
            st.integers(min_value=1, max_value=10)   # num metrics
        ),
        elements=st.floats(min_value=-100, max_value=100)
    ),
    config=sort_configs(),
    exclusions=exclusions_dicts()
)
def test_property_analyze_metrics(metrics, config, exclusions):
    manager = TaskManager()
    result = manager.analyze_task_metrics(
        metrics,
        config=config,
        exclusions=exclusions
    )

    # Property 1: Result is a valid numpy array
    assert isinstance(result, np.ndarray)

    # Property 2: All indices are valid
    assert np.all(result >= 0)
    assert np.all(result < len(metrics))

    # Property 3: No excluded indices in result
    for idx in exclusions['indices']:
        assert idx not in result

    # Property 4: Result has no duplicates
    assert len(result) == len(np.unique(result))
```

This will generate hundreds of test inputs automatically covering edge cases!

## Example Test Cases

### Testing with custom class:
```python
config = SortConfig(reverse_order=True, stability_required=False)
result = manager.analyze_task_metrics(metrics, config=config)
```

### Testing with container:
```python
exclusions = {'indices': [0, 5, 10], 'threshold': 0.7}
result = manager.analyze_task_metrics(metrics, exclusions=exclusions)
```

### Testing with numpy arrays:
```python
metrics = np.array([[1, 2], [3, 4], [5, 6]])
weights = np.array([0.6, 0.4])
result = manager.analyze_task_metrics(metrics, weights=weights)
```

### Testing all together:
```python
result = manager.analyze_task_metrics(
    metrics_array=np.random.rand(10, 4),
    weights=np.array([0.4, 0.3, 0.2, 0.1]),
    config=SortConfig(reverse_order=False, stability_required=True),
    exclusions={'indices': [2, 7], 'threshold': 0.5}
)
```
