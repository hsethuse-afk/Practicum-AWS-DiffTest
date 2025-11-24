# Benchmarking

This document describes how to benchmark DiffTest using the HumanEval dataset.

## HumanEval Batch Benchmarking

The tool supports batch benchmarking on the entire HumanEval dataset (172 programming tasks) with automatic timeout handling to prevent long-running tests.

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

### Timeout Feature

Batch mode automatically applies a **5-second timeout** per test by default to prevent hanging on problematic test cases. Each test runs in a separate subprocess with a hard timeout - if the test doesn't complete within the timeout, the process is forcefully terminated. Tests exceeding the timeout are marked as failed with a timeout error. You can customize the timeout using `--timeout <seconds>`.

**Note:** The timeout uses multiprocessing with process-level termination, ensuring even the most stubborn hanging tests (infinite loops, stuck hypothesis generation, etc.) are killed reliably. Each test runs in complete isolation to prevent cascading timeouts.

### Output

The batch mode provides:
- **Results file**: Automatically saved as `benchmark_results_YYYYMMDD_HHMMSS.json` with complete test data
- **Summary**: Total test cases, passed/failed counts, success rate (printed at the end)
- **Detailed results**: Per-task breakdown showing:
  - Task ID and function name
  - Tool result (difference found or not)
  - Expected result (from dataset)
  - Statistics (total examples, mismatches)
  - Failure reasons

**Note:** The summary is printed at the very end to avoid being lost in output overflow.

Example output:
```
================================================================================
BENCHMARKING SUMMARY
================================================================================
Total test cases: 172
 Passed: 150
 Failed: 22
Success rate: 87.2%

================================================================================
DETAILED RESULTS
================================================================================

 HumanEval/0 (has_close_elements)
   Tool result: No difference
   Expected: No difference
   Total examples: 200
   Mismatches: 0

 HumanEval/5 (intersperse)
   Tool result: Difference found
   Expected: No difference
   Total examples: 200
   Mismatches: 15
   Reason: output mismatch detected
```

### Programmatic Access

Use `get_difference()` to retrieve simple result summaries:

```python
from dt.orchestrator import Orchestrator

orch = Orchestrator()
result = orch.run_pair("a.py", "b.py", "func_name", auto_approve=True)

# Get simplified result
diff = orch.get_difference(result)
# Returns: {"difference_found": bool, "total_examples": int,
#           "mismatches": int, "successes": int, "reason": str}
```
