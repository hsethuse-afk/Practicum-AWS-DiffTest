# Test Case: grab_f111c65a

**Project:** 01_grab

**Commit:** 0896bbd58268219e1a6dceeeb3a9cb973e3f90cc

**File:** grab/document.py

## Changed Functions

- `build_html_tree()`

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
