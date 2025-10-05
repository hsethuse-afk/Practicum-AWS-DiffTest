
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