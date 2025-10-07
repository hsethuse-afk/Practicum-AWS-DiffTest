# RightTyper Workflow - The Correct Way

## 🎯 Understanding RightTyper

**RightTyper is a DYNAMIC type inference tool** - it needs to SEE how functions are called to infer their types.

### ❌ Wrong Way (Static Analysis):
```bash
# This WON'T work well - no execution context
python3 -m righttyper src/testsample/a.py
# Result: def maximum(arr: Any, k: Any) -> Any:
```

### ✅ Correct Way (With Execution Context):
```bash
# Run RightTyper on a TEST file that CALLS the function
python3 -m righttyper tests/test_maximum.py
# Result: def maximum(arr: list[int], k: int) -> list[int]:
```

---

## 📋 Complete Workflow for HumanEval

### Step 1: Create Test File with Execution Context

From the `rightTyperTest` branch pattern, create a test file:

```python
# tests/test_humaneval_maximum.py
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Import the function
from testsample.a import maximum

# Create test cases that CALL the function
def test_maximum():
    # These calls give RightTyper execution context
    assert maximum([1, 2, 3, 4], 2) == [3, 4]
    assert maximum([-3, -4, 5], 3) == [-4, -3, 5]
    assert maximum([4, -4, 4], 2) == [4, 4]
    assert maximum([], 0) == []

# Run the tests
if __name__ == "__main__":
    test_maximum()
    print("✅ Tests passed!")
```

### Step 2: Run RightTyper on TEST File

```bash
cd /home/intern/Practicum/Practicum-AWS-DiffTest
source src/.venv/bin/activate

# Run RightTyper on the TEST file (not the source file!)
python3 -m righttyper --all-files tests/test_humaneval_maximum.py
```

**What happens:**
1. RightTyper executes `tests/test_humaneval_maximum.py`
2. Sees calls like: `maximum([1, 2, 3, 4], 2)`
3. Infers: `arr` is `list[int]`, `k` is `int`, return is `list[int]`
4. Modifies `src/testsample/a.py` to add annotations:
   ```python
   def maximum(arr: list[int], k: int) -> list[int]:
       ...
   ```

### Step 3: Run Differential Testing

```bash
# Now the function has type annotations!
python3 src/run_ab.py \
    --a src/testsample/a.py \
    --b src/testsample/b.py \
    --func maximum \
    --max-examples 100
```

**Result:**
- Hypothesis generates ONLY `list[int]` and `int` inputs
- 100% success rate (or finds real bugs!)

---

## 🔄 Automated Workflow (What orchestrator.py does)

### Current Implementation:

```
User runs: run_ab.py --a a.py --b b.py --func maximum

↓

Orchestrator.run_pair():
├── 1. Load functions (a.py, b.py)
├── 2. Check if types missing → YES
├── 3. use_righttyper=True?
│   ├── YES: Try to run RightTyper CLI
│   │   ├── Copy files to temp directory
│   │   ├── Run: python3 -m righttyper --overwrite temp/a.py
│   │   ├── Problem: No execution context!
│   │   └── Result: Infers "Any" types (not useful)
│   └── NO: Skip RightTyper
├── 4. Reload functions (now with Any annotations)
└── 5. Generate strategies → Falls back to heuristics

↓

StrategySynthesizer:
├── See annotations are "Any"
├── Skip them (our fix)
└── Fallback to mixed strategies

↓

Hypothesis generates random types → Many failures
```

### The Problem with Current Orchestrator:
**RightTyper is run on SOURCE files without execution context!**

---

## ✅ Solution: Two-Step Process

### For HumanEval (Recommended):

#### Step 1: Pre-process with RightTyper (ONE TIME)
```bash
# For each HumanEval task, create a test file
# tests/test_humaneval_10.py

from src.humaneval.task_10 import has_close_elements

def test_has_close_elements():
    assert has_close_elements([1.0, 2.0, 3.0], 0.5) == False
    assert has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3) == True

# Then run RightTyper
python3 -m righttyper --all-files tests/test_humaneval_10.py
```

#### Step 2: Run Differential Testing
```bash
python3 src/run_ab.py \
    --a humaneval/task_10_original.py \
    --b humaneval/task_10_modified.py \
    --func has_close_elements \
    --max-examples 200
```

---

## 📝 What You Need to Do

### Option 1: Manual Annotation (Quick)
Just add type annotations to `src/testsample/a.py`:

```python
def maximum(arr: list[int], k: int) -> list[int]:
    """
    Given an array arr of integers and a positive integer k, return a sorted list
    of length k with the maximum k numbers in arr.
    """
    if k == 0:
        return []
    arr.sort()
    ans = arr[-k:]
    return ans
```

Then run:
```bash
python3 src/run_ab.py --a src/testsample/a.py --b src/testsample/b.py --func maximum --max-examples 50
```

### Option 2: Use RightTyper with Execution Context (Proper Way)

1. **Create test file:**
```bash
mkdir -p tests
cat > tests/test_maximum.py << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from testsample.a import maximum

def test_maximum():
    assert maximum([1, 2, 3, 4], 2) == [3, 4]
    assert maximum([-3, -4, 5], 3) == [-4, -3, 5]
    assert maximum([4, -4, 4], 2) == [4, 4]

if __name__ == "__main__":
    test_maximum()
    print("✅ All tests passed!")
EOF
```

2. **Run RightTyper:**
```bash
source src/.venv/bin/activate
python3 -m righttyper --all-files tests/test_maximum.py
```

3. **Check annotations were added:**
```bash
head -5 src/testsample/a.py
# Should show: def maximum(arr: list[int], k: int) -> list[int]:
```

4. **Run differential testing:**
```bash
python3 src/run_ab.py --a src/testsample/a.py --b src/testsample/b.py --func maximum --max-examples 50
```

---

## 🎯 Summary

### Key Points:
1. **RightTyper MUST have execution context** (test files that call the function)
2. **Custom RightTyper has been REMOVED** - we use only the real one
3. **Two-step process:** First annotate with RightTyper, then run differential testing
4. **For HumanEval:** Create test files per task, run RightTyper, then test

### Files Modified:
- ✅ Removed: `src/dt/righttyper.py` (custom class)
- ✅ Updated: `src/dt/strategies.py` (no custom RightTyper)
- ✅ Updated: `src/dt/orchestrator.py` (use_righttyper=True by default)

### Next Step:
Choose Option 1 (quick manual annotation) or Option 2 (proper RightTyper workflow)
