
# Differential Testing Framework

  

A property-based differential testing framework using Hypothesis for automatic test generation.

  

## Features

  

- 🔍 **Automatic Type Discovery** - Infers types from test files using RightTyper when annotations are missing

- 🎯 **Property-Based Testing** - Generates test inputs using Hypothesis strategies

- ⚙️ **Configurable** - Customize test generation parameters (ranges, sizes, etc.)

- 📊 **Coverage Support** - Optional code coverage reporting with Slipcover

  

## Quick Start

  

### Run Differential Test by File Path

  

```bash

cd  src

python  run_ab.py  --a  testsample/a.py  --b  testsample/b.py  --func  has_close_elements

```

  

**With type inference from test file:**

```bash

python  run_ab.py  --a  a.py  --b  b.py  --func  my_function  --test-file  test.py

```

  

### Run HumanEval Task by ID

  

```bash

cd  src

python  run_by_taskid.py  --t  HumanEval/10

```

  

Test file is automatically used for type inference.

  

### Run All Tests

  

```bash

cd  src

python  run_all_tests.py  --jsonl-results  testsample/samples.jsonl_results.jsonl

```

  

## Options

  

-  `--max-examples N` - Number of test cases to generate (default: 200)

-  `--log MODE` - Logging: `s`ilent, `n`ormal, `v`erbose, `d`ebug (default: normal)

-  `--test-file PATH` - Test file for type inference (run_ab.py)

-  `--coverage` - Generate coverage report (run_by_taskid.py)

  

## Configuration

  

Customize test generation in [src/dt/strategy/strategy_config.py](src/dt/strategy_config.py):

  

```python

class  StrategyConfig:

INT_MIN_VALUE  =  -50

INT_MAX_VALUE  =  50

STRING_MAX_SIZE  =  10

LIST_MAX_SIZE  =  10

# ... see STRATEGY_CONFIG.md for details

```

  

See [src/dt/strategy/STRATEGY_CONFIG.md](src/dt/STRATEGY_CONFIG.md) for customization guide.

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

## Current Capabilities & Limitations

### ✅ Fully Supported
- **Module-level functions** - Direct differential testing
- **Git diff parsing** - Automatic function extraction from diffs
- **Virtual environment isolation** - Clean dependency management
- **Automatic type inference** - Using RightTyper and test files
- **Multi-version testing** - Old vs new comparison

### ⚠️ Partially Supported
- **Class methods detection** - Can identify and report class methods from diffs
- **Class method extraction** - Full file context preserved in temp files

### ❌ Not Yet Supported
- **Class methods testing** - Currently filtered out at pairing stage
- **Class instantiation** - No automatic constructor parameter inference
- **Stateful method testing** - Methods requiring specific object state
- **Mock object creation** - Complex dependency injection

---

## Analysis: Current Implementation Gap

**Last Updated:** 2025-10-27

### Core Issue: Class Method Testing Pipeline

While the framework successfully identifies and parses class methods from git diffs, they cannot be tested due to architectural gaps in the testing pipeline.

#### What Works ✅
1. **Git Diff Parsing** ([git_diff_parser.py:285-306](src/dt/git_diff_parser.py#L285-L306))
   - Correctly identifies class methods using AST
   - Extracts method name, class name, line ranges
   - Preserves full file content (old and new versions)

2. **Temp File Creation** ([temp_file_builder.py:64-70](src/dt/temp_file_builder.py#L64-L70))
   - Creates temp files with complete class definitions
   - Maintains all imports and dependencies

#### What Blocks Testing ❌

**Problem 1: Explicit Class Method Filtering**
- Location: [diffpairer.py:104-107](src/dt/diffpairer.py#L104-L107)
- Issue: Class methods are intentionally filtered out
```python
module_level_funcs = [
    f for f in modified_funcs
    if not f.is_class_method  # ❌ Blocks all class methods
]
```

**Problem 2: Function Loader Limitations**
- Location: [harness.py:83-86](src/dt/harness.py#L83-L86)
- Issue: Only accepts `types.FunctionType`, rejects methods
- Missing: Class loading, instantiation, method binding logic

---

## Next Steps: Roadmap to Class Method Support

### Phase 1: Basic Class Method Testing (Priority: HIGH)
**Goal:** Support simple class methods with no-arg constructors

**Tasks:**
1. Remove class method filter in [diffpairer.py:104-107](src/dt/diffpairer.py#L104-L107)
2. Extend `HarnessBuilder` to load classes and methods
   - Add `_load_class_from_file(path, class_name)`
   - Add `_create_simple_instance(cls)` for no-arg constructors
   - Modify `build()` to handle both functions and methods
3. Update `ABRunner` to handle bound methods
   - Detect if callable is a method
   - Handle instance lifecycle
4. Update `StrategySynthesizer` to skip `self` parameter
   - Filter out `self` from parameter inspection
   - Generate strategies only for actual method arguments

**Acceptance Criteria:**
- Can test class methods with `__init__(self)` (no parameters)
- Example: `class Counter: def increment(self, n: int)`

### Phase 2: Constructor Parameter Inference (Priority: MEDIUM)
**Goal:** Instantiate classes with constructor parameters

**Tasks:**
1. Implement constructor parameter discovery
   - Extract `__init__` signature
   - Infer types from test files (similar to method parameters)
2. Add fixture/factory pattern support
   - Look for test fixtures in test files
   - Support common patterns (e.g., `@pytest.fixture`)
3. Add manual override mechanism
   - Allow users to provide constructor args via config

**Acceptance Criteria:**
- Can test: `class Database: def __init__(self, host: str, port: int)`
- Constructor args inferred from test files or user config

### Phase 3: Advanced Features (Priority: LOW)
**Goal:** Support complex scenarios

**Tasks:**
1. State management for stateful methods
2. Mock/stub integration for external dependencies
3. Static methods and class methods (`@staticmethod`, `@classmethod`)
4. Property and descriptor testing

---

## Technical Debt & Known Issues

1. **Git Content Retrieval** ([git_diff_parser.py:195-213](src/dt/git_diff_parser.py#L195-L213))
   - Returns `None` if no commit provided
   - Should support extracting old version from diff hunks

2. **Dependency Resolution** ([temp_file_builder.py:98-122](src/dt/temp_file_builder.py#L98-L122))
   - `build_with_dependencies()` not implemented
   - Currently relies on full file inclusion

3. **Error Handling**
   - Limited error messages when class methods are filtered out
   - Users not informed why no tests run

## Example: Current Behavior with Class Methods

```bash
$ python src/run_diff_repo.py \
    --diff src/testsample/changes.diff \
    --repo https://github.com/lorien/grab.git \
    --commit c6b703ace922365cf49526297bd577079b155f88

📋 Found 2 modified function(s)/method(s):

📦 Class methods (extracted but not tested yet): 2
   - Urllib3Transport.request() at lines 233-314
   - Urllib3Transport.prepare_response() at lines 327-444

============================================================
📊 Testing Summary
============================================================
Total functions tested: 0  ← ❌ Nothing tested
✅ Passed: 0
❌ Failed: 0
```

After Phase 1 implementation, the same command should test both methods.