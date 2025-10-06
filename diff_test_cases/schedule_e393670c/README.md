# Test Case: schedule_e393670c

**Project:** 04_schedule

**Commit:** 2dcb5833cdf2b7d7a1bda90c19e2fb7e373e66df

**File:** schedule/__init__.py

## Changed Functions

- `__init__()`
- `_schedule_next_run()`

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
