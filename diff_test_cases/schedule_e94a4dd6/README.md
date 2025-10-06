# Test Case: schedule_e94a4dd6

**Project:** 04_schedule

**Commit:** a38862005fb775521d5482e5be4affcd10eebb15

**File:** schedule/__init__.py

## Changed Functions

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
