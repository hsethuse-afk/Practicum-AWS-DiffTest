#!/usr/bin/env python3
"""
Batch processing script for SWE-bench instances.

Reads an Excel file with instance IDs, runs differential testing on each,
and saves results to a new Excel file.
"""

import argparse
import sys
import os
import pandas as pd
from datetime import datetime
import traceback
from io import StringIO

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from dt.orchestrator import Orchestrator
from utilities.coverage_runner import handle_coverage


def _save_formatted_excel(df: pd.DataFrame, output_path: str):
    """
    Save DataFrame to Excel with proper formatting.

    - Truncates log entries to prevent format issues
    - Sets proper column widths
    - Applies formatting to headers
    """
    # Truncate log entries to prevent format issues
    # Keep the LATEST messages (truncate from the beginning) since valuable results are at the end
    if 'log' in df.columns:
        df = df.copy()
        max_log_length = 5000  # Increased from 1000 to capture more valuable information
        df['log'] = df['log'].apply(
            lambda x: (
                '...[earlier messages truncated]\n' + str(x)[-max_log_length:]
                if pd.notna(x) and len(str(x)) > max_log_length
                else x
            )
        )

    try:
        # Try to use openpyxl for better formatting
        from openpyxl.styles import Font, PatternFill, Alignment

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Results')

            worksheet = writer.sheets['Results']

            # Set column widths
            column_widths = {
                'instance_id': 30,
                'status': 12,
                'functions_tested': 18,
                'functions_passed': 18,
                'functions_failed': 18,
                'report_paths': 60,
                'log': 80,
                'Environment Builder': 20,
                'Function': 20,
                'Overall Support': 20,
                'Notes': 50,
            }

            for idx, col in enumerate(df.columns, 1):
                col_letter = worksheet.cell(row=1, column=idx).column_letter
                width = column_widths.get(col, 15)
                worksheet.column_dimensions[col_letter].width = width

            # Format header row
            header_font = Font(bold=True)
            header_fill = PatternFill(start_color='D3D3D3', end_color='D3D3D3', fill_type='solid')

            for cell in worksheet[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center', vertical='center')

            # Wrap text in log and Notes columns
            for col_name in ['log', 'Notes']:
                if col_name in df.columns:
                    col_idx = df.columns.tolist().index(col_name) + 1
                    for row in range(2, len(df) + 2):
                        cell = worksheet.cell(row=row, column=col_idx)
                        cell.alignment = Alignment(wrap_text=True, vertical='top')

            # Make report_paths clickable hyperlinks
            if 'report_paths' in df.columns:
                col_idx = df.columns.tolist().index('report_paths') + 1
                for row_num in range(2, len(df) + 2):
                    cell = worksheet.cell(row=row_num, column=col_idx)
                    cell_value = str(cell.value) if cell.value else ""

                    # If the cell contains file:// URLs, make them clickable
                    if cell_value and 'file://' in cell_value:
                        # Split multiple URLs if present
                        urls = [u.strip() for u in cell_value.split(';')]
                        if urls:
                            # Use the first URL as the hyperlink
                            first_url = urls[0]
                            cell.hyperlink = first_url
                            cell.style = 'Hyperlink'
                            # Show all URLs in the cell
                            cell.value = cell_value

                    cell.alignment = Alignment(wrap_text=True, vertical='top')

    except ImportError:
        # Fallback to basic Excel output if openpyxl is not available
        df.to_excel(output_path, index=False)


def fetch_dataset_entry(instance_id: str):
    """Fetch a single entry from SWE-bench parquet file by instance ID"""
    parquet_path = os.path.join(
        os.path.dirname(__file__),
        "src",
        "utilities",
        "swe-bench",
        "SWE-bench_verified.parquet",
    )

    if not os.path.exists(parquet_path):
        raise FileNotFoundError(
            f"Parquet file not found at: {parquet_path}"
        )

    df = pd.read_parquet(parquet_path)
    matching_rows = df[df["instance_id"] == instance_id]

    if matching_rows.empty:
        raise ValueError(
            f"Instance ID '{instance_id}' not found in dataset"
        )

    row = matching_rows.iloc[0]

    return {
        "instance_id": row["instance_id"],
        "repo": row["repo"],
        "base_commit": row["base_commit"],
        "patch": row["patch"],
    }


def run_single_instance(
    instance_id: str,
    max_examples: int = 200,
    log_mode: int = 2,
    seed: int = None,
    install_deps: bool = True,
):
    """
    Run differential testing on a single SWE-bench instance.

    Returns:
        dict: Result summary with keys:
            - instance_id: str
            - status: "success" | "error" | "not_found"
            - error_message: str (if error)
            - functions_tested: int
            - functions_passed: int
            - functions_failed: int
            - function_details: list of dict with function-level results
            - report_paths: str (paths to generated HTML reports)
    """
    result = {
        "instance_id": instance_id,
        "status": "error",
        "log": "",
        "functions_tested": 0,
        "functions_passed": 0,
        "functions_failed": 0,
        "report_paths": "",
    }

    # Capture all output to log
    log_buffer = StringIO()
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    class TeeOutput:
        def __init__(self, *outputs):
            self.outputs = outputs
        def write(self, data):
            for output in self.outputs:
                output.write(data)
        def flush(self):
            for output in self.outputs:
                output.flush()

    try:
        # Redirect stdout/stderr to capture log
        sys.stdout = TeeOutput(original_stdout, log_buffer)
        sys.stderr = TeeOutput(original_stderr, log_buffer)

        print(f"\n{'='*80}")
        print(f"Processing: {instance_id}")
        print(f"{'='*80}")

        # Fetch entry from dataset
        entry = fetch_dataset_entry(instance_id)

        repo = entry["repo"]
        base_commit = entry["base_commit"]
        patch_content = entry["patch"]

        if not patch_content or not repo or not base_commit:
            result["status"] = "error"
            result["log"] = "Missing required data in dataset entry"
            return result

        print(f"✓ Repository: {repo}")
        print(f"✓ Base commit: {base_commit[:8]}")
        print(f"✓ Patch size: {len(patch_content)} bytes")

        # Initialize orchestrator
        orch = Orchestrator(log_mode=log_mode)

        # Construct repo URL
        repo_url = f"https://github.com/{repo}.git"

        # Run differential testing
        results = orch.run_base_and_patch_from_repo(
            repo_url=repo_url,
            base_commit=base_commit,
            patch_content=patch_content,
            func_name=None,  # Test all functions
            selected_functions=None,
            interactive_select=False,  # Non-interactive mode
            max_examples=max_examples,
            auto_approve=True,  # Auto-approve test strategies
            report_path=None,
            seed=seed,
            install_deps=install_deps,
        )

        # Process results
        result["status"] = "success"
        result["functions_tested"] = len(results)
        result["functions_passed"] = sum(1 for r in results if r.passed)
        result["functions_failed"] = len(results) - result["functions_passed"]

        # Extract report paths and URLs from log
        import re
        log_content = log_buffer.getvalue()

        # Extract file paths
        report_pattern = r'📊 HTML Report generated: (.+?\.html)'
        reports = re.findall(report_pattern, log_content)

        # Extract file:// URLs
        url_pattern = r'Open in browser: (file://.+?\.html)'
        urls = re.findall(url_pattern, log_content)

        if urls:
            # Prefer URLs as they're clickable
            result["report_paths"] = "; ".join(urls)
        elif reports:
            # Fallback to file paths
            result["report_paths"] = "; ".join(reports)

        print(f"\n✅ Success: {result['functions_passed']}/{result['functions_tested']} functions passed")

    except FileNotFoundError as e:
        result["status"] = "not_found"
        print(f"❌ Not found: {e}")

    except Exception as e:
        result["status"] = "error"
        print(f"❌ Error: {e}")
        traceback.print_exc()

    finally:
        # Restore original stdout/stderr
        sys.stdout = original_stdout
        sys.stderr = original_stderr

        # Save captured log
        result["log"] = log_buffer.getvalue()
        log_buffer.close()

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Batch process SWE-bench instances from Excel file"
    )

    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Input Excel file with instance_id column",
    )
    parser.add_argument(
        "--sheet",
        type=str,
        default=None,
        help="Sheet name or index (0-based) to read from Excel file. If not specified, reads first sheet.",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output Excel file for results",
    )
    parser.add_argument(
        "--max-examples",
        type=int,
        default=200,
        help="Number of test cases to generate per instance (default: 200)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible test generation (optional)",
    )
    parser.add_argument(
        "--log",
        type=str,
        default="N",
        help="Logging mode: (s)ilent, (n)ormal, (v)erbose, (d)ebug",
    )
    parser.add_argument(
        "--no-install-deps",
        action="store_true",
        help="Skip dependency installation",
    )
    parser.add_argument(
        "--start-from",
        type=int,
        default=0,
        help="Start processing from this row index (0-based, for resuming)",
    )

    args = parser.parse_args()

    # Handle coverage
    handle_coverage()

    # Parse log mode
    val = args.log.lower()
    log_mode = 2  # Normal

    if val in ("s", "silent"):
        log_mode = 1
    elif val in ("v", "verbose"):
        log_mode = 3
    elif val in ("d", "debug"):
        log_mode = 4

    # Read input Excel
    print(f"📖 Reading input file: {args.input}")

    # Determine which sheet to read
    sheet_name = args.sheet
    if sheet_name is not None:
        # Try to convert to integer if it's a number (for sheet index)
        try:
            sheet_name = int(sheet_name)
            print(f"📄 Reading sheet at index: {sheet_name}")
        except ValueError:
            # It's a sheet name string
            print(f"📄 Reading sheet: {sheet_name}")
    else:
        print(f"📄 Reading first sheet (default)")
        sheet_name = 0

    try:
        # First, list available sheets
        excel_file = pd.ExcelFile(args.input)
        available_sheets = excel_file.sheet_names
        print(f"📋 Available sheets: {', '.join(available_sheets)}")

        # Read the specified sheet
        input_df = pd.read_excel(args.input, sheet_name=sheet_name)

        # Show which sheet was actually read
        if isinstance(sheet_name, int):
            actual_sheet = available_sheets[sheet_name] if sheet_name < len(available_sheets) else "Unknown"
            print(f"✓ Reading sheet: '{actual_sheet}' (index {sheet_name})")
        else:
            print(f"✓ Reading sheet: '{sheet_name}'")

    except Exception as e:
        print(f"❌ Error reading input file: {e}")
        sys.exit(1)

    if "instance_id" not in input_df.columns:
        print("❌ Error: Input Excel must have 'instance_id' column")
        sys.exit(1)

    # Filter out empty instance_ids
    input_df = input_df[input_df["instance_id"].notna()]

    total_instances = len(input_df)
    print(f"📊 Found {total_instances} instances to process")

    if args.start_from > 0:
        print(f"⏭️  Starting from row {args.start_from}")
        input_df = input_df.iloc[args.start_from:]

    # Prepare results storage
    results_data = []

    # Process each instance
    start_time = datetime.now()

    for idx, row in input_df.iterrows():
        instance_id = row["instance_id"]

        print(f"\n[{idx + 1}/{total_instances}] Processing: {instance_id}")

        result = run_single_instance(
            instance_id=instance_id,
            max_examples=args.max_examples,
            log_mode=log_mode,
            seed=args.seed,
            install_deps=not args.no_install_deps,
        )

        # Combine original row data with results
        result_row = {
            "instance_id": instance_id,
            "status": result["status"],
            "functions_tested": result["functions_tested"],
            "functions_passed": result["functions_passed"],
            "functions_failed": result["functions_failed"],
            "report_paths": result.get("report_paths", ""),
            "log": result["log"],
        }

        # Add any original columns from input
        for col in input_df.columns:
            if col not in result_row:
                result_row[col] = row[col]

        results_data.append(result_row)

        # Save intermediate results after each instance with formatting
        results_df = pd.DataFrame(results_data)
        _save_formatted_excel(results_df, args.output)
        print(f"💾 Intermediate results saved to: {args.output}")

    # Final save with formatting
    results_df = pd.DataFrame(results_data)
    _save_formatted_excel(results_df, args.output)

    end_time = datetime.now()
    duration = end_time - start_time

    # Summary
    print(f"\n{'='*80}")
    print(f"📊 Batch Processing Complete")
    print(f"{'='*80}")
    print(f"Total instances: {total_instances}")
    print(f"Successful: {sum(1 for r in results_data if r['status'] == 'success')}")
    print(f"Errors: {sum(1 for r in results_data if r['status'] == 'error')}")
    print(f"Not found: {sum(1 for r in results_data if r['status'] == 'not_found')}")
    print(f"Duration: {duration}")
    print(f"\n✅ Results saved to: {args.output}")


if __name__ == "__main__":
    main()
