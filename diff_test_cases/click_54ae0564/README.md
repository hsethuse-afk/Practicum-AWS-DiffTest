# Test Case: click_54ae0564

**Project:** 10_click

**Commit:** 555fa9bb37770a6845a98be60b0c84876775552e

**File:** src/click/core.py

## Changed Functions

- `close()`
- `__exit__()`

## Files

- `before.py` - Code before the change
- `after.py` - Code after the change
- `changes.diff` - Git diff showing the changes
- `metadata.json` - Test case metadata

## Usage

Run your type inference tool on both versions:

```bash
# Run on before version
python -m righttyper before.py > before_types.out

# Run on after version
python -m righttyper after.py > after_types.out

# Compare the results
diff before_types.out after_types.out
```
