# Test Case: PythonRobotics_4c77be3a

**Project:** 02_PythonRobotics

**Commit:** 0e93ecb66957c5ff6642252c6ca3290b0955d63e

**File:** PathPlanning/RRT/rrt_with_pathsmoothing.py

## Changed Functions

- `line_collision_check()`
- `path_smoothing()`
- `main()`

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
