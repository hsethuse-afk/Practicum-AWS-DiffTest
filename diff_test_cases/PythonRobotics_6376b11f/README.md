# Test Case: PythonRobotics_6376b11f

**Project:** 02_PythonRobotics

**Commit:** 4ffd8e76e3429daaeb85a2db0764e7af71604af3

**File:** PathPlanning/DStarLite/d_star_lite.py

## Changed Functions

- `__init__()`
- `is_obstacle()`
- `initialize()`
- `detect_changes()`

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
