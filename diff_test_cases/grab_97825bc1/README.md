# Test Case: grab_97825bc1

**Project:** 01_grab

**Commit:** c6b703ace922365cf49526297bd577079b155f88

**File:** grab/transport/urllib3.py

## Changed Functions

- `request()`
- `prepare_response()`

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
