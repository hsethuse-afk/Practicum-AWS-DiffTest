# Differential Testing Data Extraction Summary

## Overview

Successfully extracted 33 code change diffs from 6 open-source Python projects and generated 9 high-quality differential test cases. These test cases can be used to evaluate type inference tools (such as righttyper) during code evolution.

## Source Projects

Extracted test data from the following projects:

1. **01_grab** - Web scraping framework
2. **02_PythonRobotics** - Python code collection for robotics algorithms
3. **03_flask-api** - Flask extensions for building APIs
4. **04_schedule** - Job scheduling for humans
5. **05_Pillow** - Python Imaging Library
6. **10_click** - Command line interface creation kit

## Data Extraction Pipeline

### 1. Clone Repositories and Extract Diffs (`extract_diffs.py`)
- Cloned all project git repositories (depth 100 commits)
- Identified commits containing Python file changes
- Extracted before/after code versions and diffs for each commit
- **Result**: 33 raw diffs

### 2. Analysis and Categorization (`analyze_diffs.py`)
Performed intelligent analysis and categorization of extracted diffs:

#### Categorization Results:
- **Trivial changes**: 22
  - Version number updates
  - Documentation updates
  - Configuration file changes
  - Very small changes (<5 lines)

- **Function changes without type hints**: 4 ⭐
  - **Best candidates**: Ideal for testing type inference tools
  - Contains meaningful function logic changes
  - No manual type annotations

- **Function changes with type hints**: 5
  - Function changes with type annotations
  - Useful for comparative analysis

- **Complex changes**: 2
  - Complex changes difficult to analyze automatically

### 3. Generate Test Cases (`generate_test_cases.py`)
Created structured test cases for selected diffs:

#### Test Case Structure:
```
diff_test_cases/
├── PythonRobotics_4c77be3a/
│   ├── before.py          # Code before change
│   ├── after.py           # Code after change
│   ├── changes.diff       # Git diff
│   ├── metadata.json      # Test metadata
│   └── README.md          # Test description
├── grab_97825bc1/
├── ...
├── test_index.json        # Index of all test cases
├── run_diff_tests.sh      # Batch test script
└── README.md
```

## Generated Test Cases

### Test Cases Without Type Hints (4):

1. **PythonRobotics_4c77be3a**
   - File: `PathPlanning/RRT/rrt_with_pathsmoothing.py`
   - Changed functions: `line_collision_check`, `path_smoothing`, `main`
   - Changes: Added robot_radius parameter, improved collision detection algorithm

2. **PythonRobotics_93254e26**
   - File: `PathTracking/pure_pursuit/pure_pursuit.py`
   - Changed functions: `main`, `pure_pursuit_steer_control`, `append`

3. **grab_97825bc1**
   - File: `grab/transport/urllib3.py`
   - Changed functions: `request`, `prepare_response`

4. **grab_f111c65a**
   - File: `grab/document.py`
   - Changed functions: `build_html_tree`

### Test Cases With Type Hints (5):

1. **schedule_e393670c** - `schedule/__init__.py`
2. **schedule_e94a4dd6** - `schedule/__init__.py`
3. **PythonRobotics_e0c6c237** - Time-based path planning
4. **PythonRobotics_6376b11f** - D* Lite algorithm
5. **click_54ae0564** - `src/click/core.py`

## How to Use Test Cases

### Single Test Case:
```bash
cd diff_test_cases/PythonRobotics_4c77be3a/

# Run type inference on before version
python -m righttyper before.py > before_types.out

# Run type inference on after version
python -m righttyper after.py > after_types.out

# Compare type inference results
diff before_types.out after_types.out
```

### Batch Testing:
```bash
# Run all test cases
./diff_test_cases/run_diff_tests.sh

# Or use Python script
python run_diff_tests.py
```

## Testing Objectives

These differential test cases can be used for:

1. **Type Inference Consistency Testing**
   - Verify stability of type inference tools during code evolution
   - Check if function signature changes are correctly reflected in type inference

2. **Accuracy Evaluation**
   - Compare inference results with/without type annotations
   - Evaluate tool's ability to handle parameter additions and logic changes

3. **Regression Testing**
   - Ensure tool upgrades maintain consistent inference for historical code
   - Identify unexpected changes in inference results

4. **Benchmarking**
   - Test tool performance in real-world project evolution scenarios
   - Compare performance of different type inference tools

## Directory Structure

```
.
├── extract_diffs.py              # Step 1: Script to extract diffs
├── analyze_diffs.py              # Step 2: Analyze and categorize diffs
├── generate_test_cases.py        # Step 3: Generate test cases
├── diff_test_data/               # Intermediate data
│   ├── extracted_diffs.json      # All extracted diffs
│   ├── categorized/              # Categorized diffs
│   │   ├── function_changes_no_types.json
│   │   ├── function_changes_with_types.json
│   │   ├── trivial.json
│   │   └── complex_changes.json
│   ├── individual_diffs/         # Individual diff files
│   ├── analysis_report.txt       # Analysis report
│   └── *_repo/                   # Cloned repositories
└── diff_test_cases/              # Final test cases
    ├── PythonRobotics_4c77be3a/
    ├── grab_97825bc1/
    ├── ...
    └── run_diff_tests.sh
```

## Statistics

| Metric | Count |
|--------|-------|
| Projects analyzed | 6 |
| Diffs extracted | 33 |
| Valid function changes | 9 |
| Test cases without type hints | 4 |
| Test cases with type hints | 5 |
| Total changed functions | ~15+ |

## Next Steps

1. **Run Tests**: Use `run_diff_tests.sh` to batch test all cases
2. **Analyze Results**: Check type inference consistency during code evolution
3. **Expand Dataset**:
   - Extract diffs from more projects
   - Increase extraction depth (more historical commits)
   - Add specific types of changes (e.g., refactoring, bug fixes, etc.)
4. **Automated Evaluation**: Develop automated evaluation scripts to quantify type inference accuracy and consistency

## Example Test Case Details

### PythonRobotics_4c77be3a

This is an excellent test case example demonstrating function signature and implementation evolution:

**Before Change**:
```python
def line_collision_check(first, second, obstacleList):
    # Simple collision detection
```

**After Change**:
```python
def line_collision_check(first, second, obstacle_list, robot_radius=0.0, sample_step=0.2):
    """
    Check if the line segment between `first` and `second` collides with any obstacle.
    ...
    """
    # More precise collision detection considering robot radius
```

**Testing Goals**:
- Can the inference tool correctly identify newly added parameters?
- Can it infer types from parameter default values (float)?
- Can it infer List type structures from usage context?

---

**Generation Date**: 2025-10-06
**Tool Version**: Python 3.12, righttyper
