
# Differential Testing Framework

A property-based differential testing framework using Hypothesis for automatic test generation and comparison.

## Features

- 🔍 **Automatic Type Discovery** - Infers types from test files using RightTyper when annotations are missing
- 🎯 **Property-Based Testing** - Generates test inputs using Hypothesis strategies
- 🏗️ **Class Method Support** - Tests both module-level functions and class methods with intelligent instance generation
- 📊 **HTML Reports** - Interactive, shareable HTML reports with search, filtering, and collapsible sections
- 📈 **Coverage Tracking** - Optional code coverage reporting with Slipcover integration
- ⚙️ **Configurable** - Customize test generation parameters, NumPy dtypes, and strategy behaviors
- 🔄 **Git Integration** - Compare functions across git commits
- 🎨 **Dark Mode** - HTML reports automatically adapt to system theme preferences

## Quick Start

  

### Basic Usage - Module Functions

```bash
cd src
python run_ab.py --a testsample/a.py --b testsample/b.py --func has_close_elements
```

**With type inference from test file:**
```bash
python run_ab.py --a a.py --b b.py --func my_function --test-file test.py
```

### Testing Class Methods

```bash
python run_ab.py \
  --a calculator_v1.py \
  --b calculator_v2.py \
  --func add \
  --class Calculator \
  --max-examples 500
```

The framework automatically:
- Detects constructor parameters and generates instances
- Distributes test cases across multiple instances using smart heuristics
- Shows per-instance statistics in reports

### Generating HTML Reports

Add `--report` flag to generate interactive HTML reports:

```bash
python run_ab.py \
  --a calculator_v1.py \
  --b calculator_v2.py \
  --func add \
  --class Calculator \
  --max-examples 500 \
  --report my_report.html
```

**Report features:**
- ✅ Visual status indicators and statistics
- 🔍 Search and filter mismatches
- 📊 Per-instance distribution (for class methods)
- 📋 Collapsible, scrollable sections
- 🌓 Dark mode support
- 💾 Self-contained single HTML file

### Run HumanEval Task by ID

```bash
cd src
python run_by_taskid.py --t HumanEval/10
```

Test file is automatically used for type inference.

### Run All Tests

```bash
cd src
python run_all_tests.py --jsonl-results testsample/samples.jsonl_results.jsonl
```

## Command-Line Options

### run_ab.py

- `--a PATH` - Path to first version of the code
- `--b PATH` - Path to second version of the code
- `--func NAME` - Function name to test
- `--max-examples N` - Number of test cases to generate (default: 200)
- `--seed N` - Random seed for reproducibility
- `--test-file PATH` - Test file for type inference
- `--report PATH` - Generate HTML report at specified path
- `--auto-approve` - Skip strategy confirmation prompt
- `--log MODE` - Logging: `s`ilent, `n`ormal, `v`erbose, `d`ebug (default: normal)
- `--coverage` - Generate coverage report

## Configuration & Customization

### Strategy Configuration

Customize test generation parameters in strategy configuration files:

```python
class StrategyConfig:
    INT_MIN_VALUE = -50
    INT_MAX_VALUE = 50
    STRING_MAX_SIZE = 10
    LIST_MAX_SIZE = 10
    # ... and many more options
```

See [src/dt/strategy/STRATEGY_CONFIG.md](src/dt/STRATEGY_CONFIG.md) for complete customization guide.

### Strategy Files

The framework automatically generates strategy files that you can customize. See [Hypothesis Documentation](https://hypothesis.readthedocs.io/en/latest/reference/strategies.html#hypothesis.strategies.builds) for more customization options. The strategy file uses a structured JSON format:

```json
{
  "parameters": {
    "parameter1": {
      "type": "integers",
      "min_value": -50,
      "max_value": 50
    },
    "parameter1": {
      "type": "integers",
      "min_value": -50,
      "max_value": 50
    }
  }
}
```

**For class methods with complex types:**

```json
{
  "_comment": "Customize instance and method parameter generation",
  "parameters": {
    "points": {
      "type": "lists",
      "elements": {
        "type": "builds",
        "target": "mymodule.Point",
        "x": {
          "type": "floats",
          "min_value": -50.0,
          "max_value": 50.0
        },
        "y": {
          "type": "floats",
          "min_value": -50.0,
          "max_value": 50.0
        }
      },
      "min_size": 0,
      "max_size": 10
    },
    "threshold": {
      "type": "floats",
      "min_value": 0.0,
      "max_value": 100.0
    }
  }
}
```

The framework will:
- Generate a strategy file automatically on first run
- Prompt you to review and approve the strategy
- Allow you to edit the JSON file to customize parameters
- Reload the strategy after you make changes

## Advanced Features

### Instance Distribution for Class Methods

The framework uses intelligent heuristics to distribute test cases across instances:
- **Square Root Heuristic**: `num_instances = sqrt(max_examples)`
- **Minimum Tests**: Ensures at least 5-7 tests per instance
- **Smart Balancing**: Distributes tests evenly across instances

### Strategy Serialization

All test strategies are serialized to JSON for:
- **Reproducibility**: Re-run tests with exact same strategy
- **Review & Approval**: User can review before execution
- **Customization**: Modify strategies per function or class
- **Version Control**: Track strategy changes over time

### Coverage Integration

Coverage tracking uses Slipcover for minimal overhead:
- Shows lines executed during differential testing
- Helps identify untested code paths
- Integrates seamlessly with test execution

## Examples

### Example 1: Testing a Calculator Class

```bash
# Test the add method with custom parameters
python src/run_ab.py \
  --a examples/calculator_v1.py \
  --b examples/calculator_v2.py \
  --func add \
  --class Calculator \
  --max-examples 500 \
  --report calculator_test.html \
  --auto-approve
```

### Example 2: NumPy Function with Coverage

```bash
# Test with coverage tracking
python src/run_by_taskid.py \
  --t HumanEval/10 \
  --coverage \
  --max-examples 1000
```

### Example 3: Git Diff Testing

```bash
# Compare current commit with previous
python src/run_ab.py \
  --commit HEAD \
  --func my_function \
  --report git_diff_report.html
```

## Requirements

- Python 3.11+
- Hypothesis (property-based testing)
- Jinja2 (HTML report generation)
- Slipcover (optional, for coverage tracking)
- RightTyper (type inference)

Install dependencies:
```bash
pip install hypothesis jinja2 slipcover righttyper
```

---

## Git Diff Testing

### Run Differential Test from Git Diff

Test modified functions automatically from a git diff file:

```bash
python src/run_diff_repo.py \
  --diff src/testsample/changes.diff \
  --repo https://github.com/lorien/grab.git \
  --commit c6b703ace922365cf49526297bd577079b155f88 \
  --max-examples 200
```

**Parameters:**
- `--diff PATH` - Path to git diff file (required)
- `--repo URL` - Repository URL to clone (required)
- `--commit HASH` - Specific commit hash (optional, auto-detected from diff)
- `--max-examples N` - Number of test cases (default: 200)
- `--log MODE` - Logging level (silent/normal/verbose/debug)
- `--no-install-deps` - Skip dependency installation

**How it works:**
1. Clones the repository to a temporary directory
2. Creates an isolated virtual environment
3. Installs project dependencies (from pyproject.toml or requirements.txt)
4. Parses the diff file to identify modified functions
5. Generates test cases using Hypothesis
6. Runs differential tests comparing old vs new versions
7. Reports any behavioral differences

---

## Git Commit Testing

### Run Differential Test from a Commit

Test modified functions directly from a commit hash (no diff file needed):

```bash
python src/run_commit.py \
  --repo https://github.com/user/repo.git \
  --commit ed7facc1b108ceff12bcb412d7a98471509f41b0 \
  --max-examples 200
```

**Parameters:**
- `--repo URL` - Repository URL to clone (required)
- `--commit HASH` - Commit hash to test (required)
- `--func NAME` - Test only a specific function by name (optional)
- `--functions INDICES` - Comma-separated function indices to test, e.g., '1,2,3' or '1-3' (optional)
- `--no-interactive` - Skip interactive function selection (optional)
- `--max-examples N` - Number of test cases (default: 200)
- `--log MODE` - Logging level (silent/normal/verbose/debug)
- `--no-install-deps` - Skip dependency installation
- `--coverage` - Generate coverage report
- `--auto-approve` - Automatically approve test strategies without user confirmation

**How it works:**
1. Clones the repository to a temporary directory
2. Generates diff from the commit automatically
3. Creates an isolated virtual environment
4. Installs project dependencies
5. Parses the commit to identify modified functions
6. Generates test cases using Hypothesis
7. Runs differential tests comparing old vs new versions
8. Reports any behavioral differences

**Example with interactive function selection:**
```bash
python src/run_commit.py \
  --repo https://github.com/user/repo.git \
  --commit abc123def456
```

**Example with specific functions:**
```bash
python src/run_commit.py \
  --repo https://github.com/user/repo.git \
  --commit abc123def456 \
  --functions 1,3,5 \
  --no-interactive
```

---

## Current Capabilities & Limitations

### ✅ Fully Supported
- **Module-level functions** - Direct differential testing
- **Git diff parsing** - Automatic function extraction from diffs
- **Git commit testing** - Direct testing from commit hashes
- **Virtual environment isolation** - Clean dependency management
- **Automatic type inference** - Using RightTyper and test files
- **Multi-version testing** - Old vs new comparison
- **Interactive function selection** - Choose which functions to test
- **Coverage reporting** - Optional code coverage with Slipcover

### ⚠️ Partially Supported
- **Class methods detection** - Can identify and report class methods from diffs
- **Class method extraction** - Full file context preserved in temp files

### ❌ Not Yet Supported
- **Class methods testing** - Currently filtered out at pairing stage
- **Class instantiation** - No automatic constructor parameter inference
- **Stateful method testing** - Methods requiring specific object state
- **Mock object creation** - Complex dependency injection