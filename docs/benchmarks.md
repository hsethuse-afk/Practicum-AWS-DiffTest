# Benchmarking

This document describes how to benchmark DiffTest using datasets to evaluate its differential testing capabilities.

## Overview

DiffTest currently supports difference detection in function level between code implementations. Both benchmark datasets evaluate this capability but serve different purposes in the development and validation process:

- **HumanEval**: Sanity check and regression testing during development
- **SWE-bench**: Real-world stress testing to identify tool limitations

HumanEval helps ensure the tool works correctly on clean, isolated functions and that new changes don't break existing functionality. SWE-bench reveals what's needed to support more complex real-world scenarios—exposing gaps in the tool's current capabilities.

---

## HumanEval Dataset

### Purpose

HumanEval serves as a **sanity check and regression test** during tool development. It consists of 172 (164 original with added test for more edge cases) clean, isolated programming tasks with canonical and LLM-generated solutions. This dataset was instrumental in the early stages of development for validating core functionality and continues to ensure new changes don't break the tool.

### How It's Used

The benchmark compares canonical solutions against LLM-generated completions for the same task. For each task:
1. Extracts both the canonical and completion implementations
2. Extracts the associated test file
3. Runs DiffTest to compare the two implementations, use test file for type inference when type annotations are missing
4. Validates whether the tool correctly identifies if they are functionally equivalent

**How the code works:**
- **Extraction** ([run_human-eval.py:26-40](src/run_human-eval.py#L26-L40)): Pulls canonical solution, completion, and tests from JSONL files
- **Test Execution** ([run_human-eval.py:53-62](src/run_human-eval.py#L53-L62)): Orchestrator runs differential testing with auto-approval for batch mode
- **Timeout Protection** ([run_human-eval.py:190-198](src/run_human-eval.py#L190-L198)): Each test runs in a separate process with configurable timeout (default 5s) to prevent hanging
- **Result Validation** ([run_human-eval.py:232-262](src/run_human-eval.py#L232-L262)): Compares tool's finding against expected results and tracks pass/fail

### Why This Dataset

**Strengths:**
- Quick feedback loop for development (fast execution)
- Large dataset (172 tasks) for statistical confidence
- Clean, isolated functions make debugging easier
- Clear pass/fail validation
- Ideal for confirming the tool's core logic works

**What It Doesn't Test:**
- Real-world code complexity
- Cross-file dependencies and imports
- Complex project structures
- Edge cases in production codebases

### Usage

**Single test:**
```bash
python src/run_human-eval.py --t HumanEval/0 --max-examples 200
```

**Batch mode (all tests with 5s timeout per test):**
```bash
python src/run_human-eval.py --run-all --max-examples 200
```

**Custom timeout:**
```bash
python src/run_human-eval.py --run-all --max-examples 200 --timeout 60
```

**With validation:**
```bash
python src/run_human-eval.py --run-all --dataset ./src/utilities/human_eval/human_eval.jsonl
```

### Output

The batch mode provides:
- **Results file**: Automatically saved as `human-eval_benchmark_results_YYYYMMDD_HHMMSS.json`
- **Summary**: Total test cases, passed/failed counts, success rate
- **Detailed results**: Per-task breakdown with statistics and failure reasons

Example output:
```
================================================================================
BENCHMARKING SUMMARY
================================================================================
Total test cases: 172
✓ Passed: 150
✗ Failed: 22
Success rate: 87.2%

================================================================================
DETAILED RESULTS
================================================================================

✓ HumanEval/0 (has_close_elements)
   Tool result: No difference
   Expected: No difference
   Total examples: 200
   Mismatches: 0

✗ HumanEval/5 (intersperse)
   Tool result: Difference found
   Expected: No difference
   Total examples: 200
   Mismatches: 15
   Reason: output mismatch detected
```

---

## SWE-bench Dataset

### Purpose

SWE-bench provides a **structured framework for testing against real-world repositories**. It contains verified patches from production codebases (Django, Flask, etc.) with complete repository context. This dataset reveals where the tool struggles and what capabilities need to be added to support real-world development workflows.

### How It's Used

The benchmark applies real patches from open-source projects to identify functional differences:
1. Clones the repository at the specified base commit
2. Compares the "before" state (base commit) with the "after" state (base + patch applied)
3. Identifies which functions were modified in the patch
4. Runs differential testing on each modified function
5. Reports which functions have behavioral differences

**How the code works:**
- **Dataset Loading** ([run_swe-bench.py:17-51](src/run_swe-bench.py#L17-L51)): Reads instance data from parquet file containing repo, commit, and patch info
- **Repo Setup** ([run_swe-bench.py:190-202](src/run_swe-bench.py#L190-L202)): Orchestrator clones repository, checks out base commit, applies patch, sets up virtual environment
- **Function Selection** ([run_swe-bench.py:194-196](src/run_swe-bench.py#L194-L196)): Can test specific functions, select interactively, or test all modified functions
- **Differential Testing** ([run_swe-bench.py:190-202](src/run_swe-bench.py#L190-L202)): Compares function behavior before and after patch application with proper dependency handling

### Why This Dataset

**What It Provides:**
- Structured access to real-world patches with version control context
- Complete repository environments with actual dependencies
- Diverse Python projects with different architectural patterns
- Verifiable test cases from production code

**What It Reveals:**
- Tool performs poorly on complex real-world codebases
- Identifies missing capabilities needed for production use
- Exposes limitations in handling cross-file dependencies
- Shows challenges with complex project structures and imports
- Highlights what features need to be added to support real development scenarios

**Trade-offs:**
- Slower execution (repository cloning, dependency installation)
- More complex setup compared to HumanEval

### Usage

**Test a specific instance:**
```bash
python src/run_swe-bench.py --instance-id django__django-11099 --max-examples 200
```

**Test specific function by name:**
```bash
python src/run_swe-bench.py --instance-id django__django-11099 --func my_function
```

**Test multiple functions by index:**
```bash
python src/run_swe-bench.py --instance-id django__django-11099 --functions 1,2,3
```

**Non-interactive mode (test all modified functions):**
```bash
python src/run_swe-bench.py --instance-id django__django-11099 --no-interactive
```

**Skip dependency installation:**
```bash
python src/run_swe-bench.py --instance-id django__django-11099 --no-install-deps
```

### Output

Example output:
```
============================================================
🧪 Running Differential Tests using Base Commit + Patch
============================================================

✓ Instance ID: django__django-11099
✓ Repository: django/django
✓ Base commit: abc12345
✓ Patch size: 1234 bytes

============================================================
📊 Testing Summary
============================================================
Total functions tested: 5
✅ No Difference Found: 3
❌ Differences Found: 2

📄 Report saved to: results.html
```

## Results and Evaluation

### Evaluation Metrics

Both benchmarks track:
- **Accuracy**: Percentage of correctly identified differences
- **False Positives**: Cases where tool reports difference when none exists
- **False Negatives**: Cases where tool misses actual differences
- **Timeout Rate**: Percentage of tests that exceed time limits

### Current Results

**TBA** - Results will be added after completing benchmark runs on both datasets.

---

## Programmatic Access

For custom benchmarking or integration, use the `get_difference()` API:

```python
from dt.orchestrator import Orchestrator

orch = Orchestrator()
result = orch.run_pair("a.py", "b.py", "func_name", auto_approve=True)

# Get simplified result
diff = orch.get_difference(result)
# Returns: {"difference_found": bool, "total_examples": int,
#           "mismatches": int, "successes": int, "reason": str}
```
