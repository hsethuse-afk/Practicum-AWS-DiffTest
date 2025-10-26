# testCustomClass - Documentation Index

This directory contains a complete example and explanation of custom class support in differential testing.

## Quick Start

```bash
# Run the tests
python src/run_ab.py --a testCustomClass/a1.py --b testCustomClass/b1.py --func find_closest_points --max-examples 100

# Or use the demo script
cd testCustomClass && ./run_tests.sh
```

## Files

### Implementation Files
- **[a1.py](a1.py)** - Implementation A with custom `Point` class
- **[b1.py](b1.py)** - Implementation B with non-functional changes

### Documentation

1. **[README.md](README.md)** - Overview and usage guide
   - What the custom class does
   - How to run the tests
   - What results to expect

2. **[HOW_IT_WORKS.md](HOW_IT_WORKS.md)** ⭐ **Start here to understand the flow!**
   - Complete step-by-step explanation
   - How `typing.List[Point]` becomes `builds(Point, ...)`
   - Diagrams showing the recursive process
   - Key Python and Hypothesis features used

3. **[CODE_TRACE.md](CODE_TRACE.md)** - Detailed code walkthrough
   - Exact line numbers and file locations
   - Full call stack with all levels
   - What happens at each step
   - Return path explanation

4. **[EXAMPLE_OUTPUT.md](EXAMPLE_OUTPUT.md)** - Real test output
   - What you see when running the tests
   - Explanation of each phase
   - Insights from the output

5. **[DIFFERENCES.md](DIFFERENCES.md)** (to be created) - Side-by-side comparison
   - Shows non-functional differences between a1.py and b1.py
   - Explains why they're equivalent

### Scripts
- **[run_tests.sh](run_tests.sh)** - Automated test runner

## Learning Path

### For Understanding How It Works

1. Read [README.md](README.md) for the big picture
2. Read [HOW_IT_WORKS.md](HOW_IT_WORKS.md) for the conceptual flow
3. Read [CODE_TRACE.md](CODE_TRACE.md) for implementation details
4. Run the tests and compare with [EXAMPLE_OUTPUT.md](EXAMPLE_OUTPUT.md)

### For Quick Testing

1. Run `./run_tests.sh`
2. Or manually run commands from [README.md](README.md)

## Key Question Answered

**Q: How does `typing.List[a1.Point]` become `builds(Point, x=floats(), y=floats())`?**

**A**: The process involves:

1. **Type Decomposition** (`typing.get_origin()` and `typing.get_args()`)
   - `List[Point]` → origin: `list`, args: `(Point,)`

2. **Recursive Strategy Generation**
   - Handle `List` container
   - Recursively handle `Point` element type

3. **Hypothesis Magic** (`st.from_type()`)
   - Inspects `Point.__init__(self, x: float, y: float)`
   - Maps annotations: `float` → `st.floats()`
   - Generates: `builds(Point, x=floats(), y=floats())`

4. **Composition**
   - Wraps in `st.lists()`
   - Final: `lists(builds(Point, x=floats(), y=floats()), max_size=10)`

See [HOW_IT_WORKS.md](HOW_IT_WORKS.md) for the complete explanation!

## Technical Components

### Python Features Used
- `typing.List[T]` - Generic type annotations
- `typing.get_origin()` - Extract container type
- `typing.get_args()` - Extract type arguments
- `inspect.signature()` - Introspect function signatures

### Hypothesis Features Used
- `st.from_type()` - Automatic strategy inference from type hints
- `st.builds()` - Construct instances by calling constructors
- `st.lists()` - Generate lists with element strategies
- `st.floats()` - Generate floating-point numbers

### Custom Implementation
- Recursive type processing in `StrategySynthesizer`
- Type resolution from module namespace
- Integration with RightTyper for type inference

## Testing Summary

The differential testing framework can now:
- ✅ Handle user-defined classes with type annotations
- ✅ Automatically generate test instances
- ✅ Compare complex object outputs
- ✅ Report behavioral differences

All without manual test case writing!
