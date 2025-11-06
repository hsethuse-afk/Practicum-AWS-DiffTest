
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