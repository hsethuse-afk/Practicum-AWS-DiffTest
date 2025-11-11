import json
import sys
import os  
from coverage import CoverageData

json_report_path = "slipcover.json" 
output_db_path = ".coverage"

base_dir = os.path.abspath(os.path.dirname(__file__))

# 1. Load JSON report
try:
    with open(json_report_path, 'r') as f:
        report = json.load(f)
except FileNotFoundError:
    print(f"Error: Could not find report file: {json_report_path}", file=sys.stderr)
    print("Please run 'slipcover --json --out slipcover.json -m pytest' first.", file=sys.stderr)
    sys.exit(1)
except json.JSONDecodeError:
    print(f"Error: Could not parse JSON from {json_report_path}", file=sys.stderr)
    sys.exit(1)

# 2. Transform data for the add_lines() method
line_data_to_add = {}
files_data = report.get("files", {})

if not files_data:
    print("Error: JSON report contains no 'files' data.", file=sys.stderr)
    sys.exit(1)

print("--- Processing files and resolving to absolute paths ---")
for filename, data in files_data.items():
    executed_lines = data.get("executed_lines")
    if executed_lines is not None:
        
        # Convert the relative path from the JSON to an absolute path.
        abs_path = os.path.abspath(filename)

        print(f"  Adding file: {filename} (Resolved to: {abs_path})")
        
        line_data_to_add[abs_path] = executed_lines
    else:
        print(f"Warning: No 'executed_lines' found for {filename}")

print(f"\nProcessed coverage data for {len(line_data_to_add)} file(s).")

# 3. Use the CoverageData API to write the .coverage file
cov_data = CoverageData(basename=output_db_path)

cov_data.erase()

cov_data.add_lines(line_data_to_add)

cov_data.write()

print(f"Successfully created {output_db_path} file.")

def open_coverage_report():
    """Runs 'coverage html' and opens the report in a web browser."""
    import subprocess
    import webbrowser
    
    print("\nGenerating HTML report...")
    subprocess.run(["coverage", "html"], check=True)
    
    report_path = os.path.join(base_dir, '..', 'htmlcov', 'index.html')
    report_abs_path = os.path.abspath(report_path)
    
    print(f"Opening report: {report_abs_path}")
    webbrowser.open(f'file://{report_abs_path}')

open_coverage_report()
