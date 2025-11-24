# RightTyper Exploration

## Overview

RightTyper is a runtime type inference tool developed by AWS that analyzes Python code execution to automatically generate type annotations. Since it is a **runtime type checker**, it requires a test file that exercises the target functions to observe their runtime behavior and infer types.

## Key Requirement: Test File Necessity

**CRITICAL**: RightTyper must have a test file to run because it:
1. **Executes the test file** to trace function calls
2. **Observes runtime types** of parameters and return values during execution
3. **Analyzes the collected traces** to infer type annotations
4. **Modifies source files** to add the inferred annotations

Without a test file that calls the target functions, RightTyper has no runtime data to analyze and cannot infer types.

---

## Usage Patterns

### 1. Running Module Test - All Imported Modules

Analyze all files imported by the test file:

```bash
python -m righttyper --all-files ./tests/test.py
```

**What it does**:
- Runs `./tests/test.py`
- Traces all functions in all modules imported by the test
- Adds type annotations to all traced files

**Use case**: Comprehensive type inference across entire project

---

### 2. Specify the Function Name

Target specific functions by name using regex pattern:

```bash
python -m righttyper --all-files --include-functions "^split_words$" ./tests/test.py
```

**What it does**:
- Runs `./tests/test.py`
- Only infers types for functions matching the pattern `^split_words$` (exact match)
- Ignores all other functions

**Use case**: Selective type inference for specific functions

**Pattern examples**:
- `"^split_words$"` - Exact match for `split_words` function
- `"^process_.*"` - All functions starting with `process_`
- `".*_helper$"` - All functions ending with `_helper`

---

### 3. Specify the Python File Name

Target specific source files using regex pattern:

```bash
python -m righttyper --all-files --include-files "a.py$" ./tests/test.py
```

**What it does**:
- Runs `./tests/test.py`
- Only infers types for functions in files matching the pattern `a.py$`
- Ignores functions in all other files

**Use case**: Limit type inference to specific modules

**Pattern examples**:
- `"a.py$"` - Exact match for `a.py`
- `".*utils.py$"` - All files ending with `utils.py`
- `"src/.*\.py$"` - All Python files in `src/` directory

---

### 4. Running Numpy Test

Test RightTyper with NumPy-heavy code:

```bash
python -m righttyper ./numpy_test/numpyOut.py
```

**What it does**:
- Runs `./numpy_test/numpyOut.py` as both test file and target
- Infers types for NumPy arrays and other NumPy-specific types
- Handles complex generic types like `np.ndarray`

**Use case**: Testing type inference for scientific computing libraries

**Note**: RightTyper can infer NumPy types but may simplify complex generics (e.g., `np.ndarray[Any, DType]` → `np.ndarray`)

---

## Common Flags

| Flag | Description |
|------|-------------|
| `--all-files` | Analyze all files imported by the test file |
| `--include-functions <pattern>` | Only infer types for functions matching regex pattern |
| `--include-files <pattern>` | Only infer types in files matching regex pattern |
| `--overwrite` | Modify source files in-place |
| `--output-files` | Required when using `--overwrite` |

---

## Limitations

1. **Runtime-only**: Can only infer types for code that actually executes
2. **Test dependency**: Requires test file that exercises target functions
3. **Type simplification**: May simplify complex generic types
4. **Python 3.11+ requirement**: Uses newer typing features (`typing.Self`, `typing.Never`)

---

## See Also

- [Type Inference](type-inference.md) - Overall type inference system architecture
- [RightTyper GitHub](https://github.com/GrammaTech/righttyper) - Official RightTyper repository
- [RightTyper Engine](../src/dt/type_inference/righttyper_engine.py) - DiffTest integration implementation
