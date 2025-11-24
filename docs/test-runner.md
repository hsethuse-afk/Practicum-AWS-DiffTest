# Test Runner

## Overview

The Test Runner system executes differential tests by running two versions of code with generated test inputs and capturing their outputs. It uses Hypothesis for property-based testing, handles both regular functions and class methods, and manages test execution with timeouts and threading.

## Purpose

- **Test Execution**: Run generated test cases through both code versions
- **Output Capture**: Record return values and exceptions from test executions
- **Warning Collection**: Capture runtime warnings during test execution
- **Class Method Support**: Generate instances and distribute tests across multiple instances
- **Timeout Management**: Prevent infinite loops or hanging tests
- **Batch Testing**: Run differential tests on entire test suites (JSONL files)

## Key Components

| Component | File | Description |
|-----------|------|-------------|
| `ABRunner` | `abrunner.py` | Core differential test executor using Hypothesis |
| `TestRunner` | `test_runner.py` | High-level test runner with timeout and batch capabilities |
| `_observe()` | `abrunner.py` | Function execution wrapper that captures results and warnings |

## Dependencies

### External Libraries

- **Hypothesis**: Property-based testing framework (`hypothesis.given`, `hypothesis.strategies`)
- **warnings**: Python warnings module for capturing runtime warnings
- **threading**: For timeout implementation

### Internal Components

| Component | File | Interaction |
|-----------|------|-------------|
| `StrategySynthesizer` | `strategy/strategies.py` | Provides test input strategies |
| `ABComparator` | `comparator.py` | Consumes test results for comparison |
| `HTMLReporter` | `reporting/html_reporter.py` | Generates reports from test results |
| `Orchestrator` | `orchestrator.py` | Coordinates end-to-end test workflow |
| `StrategyPlan` | `contracts.py` | Input strategy specification |
| `RunConfig` | `contracts.py` | Test execution configuration |
| `RunResult` | `contracts.py` | Individual test case result |

### Data Flow

```
+------------------+     StrategyPlan    +------------------+
|StrategySynthesizer| ----------------> |    ABRunner      |
|                  |                     | (test executor)  |
+------------------+                     +--------+---------+
                                                  |
                                            RunResult[]
                                                  |
                    +-----------------------------+-----------------------------+
                    |                             |                             |
                    v                             v                             v
         +------------------+         +------------------+         +------------------+
         |   ABComparator   |         |   HTMLReporter   |         |  ResultCollector |
         | (compare outputs)|         | (generate report)|         | (aggregate stats)|
         +------------------+         +------------------+         +------------------+
```

## Notes

- **Property-Based Testing**: Uses Hypothesis to generate test cases automatically
- **Deterministic Execution**: Supports seeding for reproducible test runs
- **Warning Capture**: Collects all warnings for debugging and reporting
- **Instance Distribution**: For class methods, distributes tests across multiple instances using sqrt heuristic
- **Timeout Protection**: TestRunner wraps execution with thread-based timeouts
- **Exception Handling**: Captures exceptions as test outputs rather than failing the test run

---

## How It Works

### 1. ABRunner (`abrunner.py`)

The core test executor that runs differential tests using Hypothesis.

#### Main Method: `execute()`

```python
def execute(fn_a, fn_b, strat, cfg):
    """
    Execute differential tests on two functions or class methods.

    Returns: (a_results, b_results, captured_warnings)
    """
    # Check if testing class methods
    if strat.instance_strategy and strat.num_instances:
        return _execute_class_methods(fn_a, fn_b, strat, cfg)
    else:
        return _execute_functions(fn_a, fn_b, strat, cfg)
```

#### Function Testing Flow

```
+------------------------------------------------------------------+
|                     _execute_functions()                         |
|  Input: fn_a, fn_b, strategy, config                             |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|                   Configure Hypothesis settings                  |
|  - max_examples from config                                      |
|  - suppress_health_check (too_slow, filter_too_much)             |
|  - deadline=None (no timeout per example)                        |
|  - database=None (no example reuse)                              |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|                    @given(strat.arg_strategy)                    |
|  For each generated test input:                                  |
|    1. Call _observe(fn_a, args) -> (status_a, result_a)          |
|    2. Call _observe(fn_b, args) -> (status_b, result_b)          |
|    3. Append RunResult to a_results and b_results                |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|                    Return (a_results, b_results, warnings)       |
+------------------------------------------------------------------+
```

#### Class Method Testing Flow

```
+------------------------------------------------------------------+
|                  _execute_class_methods()                        |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|                   Generate Instances Upfront                     |
|  - Use strat.instance_strategy.example()                         |
|  - Generate num_instances instances                              |
|  - Handle generation errors gracefully                           |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|              Calculate examples_per_instance                     |
|  examples_per_instance = max_examples // num_instances           |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|               For each instance:                                 |
|  1. Create Hypothesis property with examples_per_instance        |
|  2. For each generated args:                                     |
|     - Prepend instance: full_args = (instance,) + args           |
|     - Call method_a(instance, *args)                             |
|     - Call method_b(instance, *args)                             |
|  3. Collect results                                              |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|          Return (a_results, b_results, warnings)                 |
|  Results include instance information                            |
+------------------------------------------------------------------+
```

#### Output Observation: `_observe()`

Captures function execution results safely:

```python
def _observe(fn, args, captured_warnings):
    """
    Execute function and capture result or exception.

    Returns: ("ret", value) or ("exc", error_string)
    """
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            result = fn(*args)

            # Record warnings
            for warning in w:
                captured_warnings.append({
                    "message": str(warning.message),
                    "category": warning.category.__name__,
                    "filename": warning.filename,
                    "lineno": warning.lineno,
                })

            return ("ret", result)
    except Exception as e:
        return ("exc", f"{type(e).__name__}: {e}")
```

**Key Features:**

- **No early termination**: Exceptions are captured, not raised
- **Warning capture**: All warnings collected in mutable list
- **Type tagging**: Output tagged as "ret" (return) or "exc" (exception)

---

### 2. TestRunner (`test_runner.py`)

High-level test runner with timeout and batch processing capabilities.

#### Method: `test_differential_behavior()`

Wraps ABRunner with thread-based timeout:

```python
def test_differential_behavior(func_a, func_b):
    """Test two functions with timeout protection."""

    result_container = [None]

    def run_test():
        try:
            strategy_plan = self.synthesizer.create_strategy(func_a)
            config = RunConfig(max_examples=50)

            compare_result = self.runner.execute(
                func_a, func_b, strategy_plan, config
            )

            if compare_result.equal:
                result_container[0] = (True, "No differences found")
            else:
                result_container[0] = (False, reason_with_example)
        except Exception as e:
            result_container[0] = (False, f"Unexpected error: {e}")

    # Run with timeout
    thread = threading.Thread(target=run_test)
    thread.daemon = True
    thread.start()
    thread.join(timeout=self.timeout_seconds)

    if thread.is_alive():
        return (False, f"Test timed out after {self.timeout_seconds} seconds")

    return result_container[0]
```

#### Method: `run_jsonl_differential_tests()`

Batch processing for HumanEval-style JSONL files:

```python
def run_jsonl_differential_tests(jsonl_path):
    """Run differential tests on JSONL results file."""

    records = load_jsonl(jsonl_path)
    passed = 0
    failed = 0

    for record in records:
        task_id = record.get("task_id", "unknown")

        # Extract functions from record
        comp_func, canon_func = extract_function_pair_from_record(record)

        # Test differential behavior
        success, error = self.test_differential_behavior(comp_func, canon_func)

        if success:
            print(f"  PASS {task_id}")
            passed += 1
        else:
            print(f"  FAIL {task_id}: {error}")
            failed += 1

    print(f"  Summary: {passed} passed, {failed} failed")
    return failed == 0
```

---

## Instance Generation for Class Methods

### Distribution Strategy

When testing class methods, ABRunner:

1. **Generates instances upfront** using `strat.instance_strategy.example()`
2. **Distributes tests** across instances using: `examples_per_instance = max_examples // num_instances`
3. **Tests each instance** with its allocated number of examples

### Example

```python
# Testing Calculator.add() with max_examples=200
# InstanceStrategyPlanner calculates: 14 instances, ~14 examples each

# Generated instances:
instances = [
    Calculator(precision=2),
    Calculator(precision=4),
    Calculator(precision=8),
    # ... 11 more instances
]

# Test distribution:
for instance in instances:
    # Run 14 test cases for this instance
    # Args: (instance, x, y)
```

### Instance Generation Error Handling

If instance generation fails:

```python
if not instances:
    error_msg = (
        "No instances generated, cannot test class methods. "
        "This usually means the constructor has constraints "
        "that aren't reflected in the strategy. "
        "Edit the strategy JSON file to add constraints."
    )
    # Add to warnings for HTML report
    # Return empty results
```

---

## Hypothesis Configuration

### Settings

```python
@settings(
    max_examples=cfg.max_examples,      # Number of test cases
    suppress_health_check=[
        HealthCheck.too_slow,            # Suppress slow test warnings
        HealthCheck.filter_too_much,     # Suppress filter warnings
    ],
    deadline=None,                       # No per-example timeout
    database=None,                       # No example persistence
)
```

### Rationale

- **max_examples**: User-configurable test count
- **suppress_health_check**: Differential testing may be slow or filter many inputs
- **deadline=None**: ABRunner doesn't enforce per-example timeouts (TestRunner provides overall timeout)
- **database=None**: Early-stage framework, no example reuse between runs

### Seed Support

For reproducible test runs:

```python
if cfg.seed is not None:
    _property = hseed(cfg.seed)(make_property())
```

---

## RunResult Data Structure

Each test case produces a `RunResult`:

```python
@dataclass
class RunResult:
    input: tuple              # Test input arguments
    output: tuple             # ("ret", value) or ("exc", error)
```

### Example Results

**Successful return:**
```python
RunResult(
    input=(5, 3),
    output=("ret", 8)
)
```

**Exception:**
```python
RunResult(
    input=(10, 0),
    output=("exc", "ZeroDivisionError: division by zero")
)
```

**Class method:**
```python
RunResult(
    input=(calculator_instance, 5, 3),
    output=("ret", 8)
)
```

---

## Warning Collection

Warnings are captured during test execution:

```python
captured_warnings = [
    {
        "message": "deprecated function called",
        "category": "DeprecationWarning",
        "filename": "/path/to/file.py",
        "lineno": 42,
    },
    # ... more warnings
]
```

These warnings are:
- Collected during `_observe()` execution
- Returned alongside test results
- Displayed in HTML reports
- Used for debugging

---

## Timeout Implementation

TestRunner uses threading for timeout protection:

```
Main Thread                    Worker Thread
     |                              |
     |------- start thread -------->|
     |                              |--- run ABRunner
     |-- join(timeout) -->          |--- execute tests
     |                              |--- collect results
     |<-- timeout expires           |
     |                              |-- still running
     |                              X (daemon thread)
```

**Daemon threads** are used so they don't prevent program exit.

---

## Integration Example

```python
# Full workflow
orchestrator = Orchestrator()

# 1. Setup (type inference + strategy generation)
strategy_plan = orchestrator.setup_differential_test(
    func_a, func_b, test_file="test.py"
)

# 2. Execute tests (ABRunner)
runner = ABRunner()
config = RunConfig(max_examples=200, seed=42)
a_results, b_results, warnings = runner.execute(
    func_a, func_b, strategy_plan, config
)

# 3. Compare (ABComparator)
comparator = ABComparator()
compare_result = comparator.compare(a_results, b_results)

# 4. Report (HTMLReporter)
reporter = HTMLReporter()
reporter.generate_report(
    test_result, a_results, b_results, strategy_plan, config, ...
)
```

---

## Performance Considerations

1. **Parallel Execution**: Tests run sequentially (Hypothesis limitation)
2. **Instance Generation**: Upfront generation avoids overhead during test execution
3. **No Database**: Skipping Hypothesis database reduces overhead
4. **Warning Capture**: Minimal performance impact
5. **Thread Timeout**: Small overhead for timeout protection

---

## Error Scenarios

### Scenario 1: Instance Generation Failure

```python
# Constructor requires positive integer
class BankAccount:
    def __init__(self, balance: int):
        if balance < 0:
            raise ValueError("Balance must be positive")

# Strategy generates negative values
# Solution: Edit strategy JSON to add min_value=0
```

### Scenario 2: Timeout

```python
# Infinite loop in one version
def buggy_function(x):
    while True:  # Hangs forever
        pass

# TestRunner will timeout after configured seconds
# Result: (False, "Test timed out after 0.5 seconds")
```

### Scenario 3: Both Functions Raise Same Exception

```python
# Both raise ValueError
a_result = ("exc", "ValueError: invalid input")
b_result = ("exc", "ValueError: invalid input")

# ABComparator will treat as match (same behavior)
```

---

## See Also

- [Strategy System](strategy-system.md) - How test inputs are generated
- [Comparator](comparator.md) - How test results are compared
- [Report Generation](report-generation.md) - How results are displayed
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/) - Property-based testing framework
