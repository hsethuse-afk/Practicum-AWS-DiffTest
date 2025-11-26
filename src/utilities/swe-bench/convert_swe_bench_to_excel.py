#!/usr/bin/env python3
"""
Convert SWE-bench_verified.parquet to Excel format.

Organizes instance IDs by repository, with each repository in a separate sheet.
"""

import os
import pandas as pd


def main():
    # Path to the parquet file
    parquet_path = os.path.join(
        os.path.dirname(__file__),
        "SWE-bench_verified.parquet",
    )

    if not os.path.exists(parquet_path):
        print(f"❌ Parquet file not found at: {parquet_path}")
        return

    print(f"📂 Loading SWE-bench dataset from: {parquet_path}")
    df = pd.read_parquet(parquet_path)
    print(f"✓ Loaded {len(df)} instances")

    # Output Excel file path
    output_path = os.path.join(
        os.path.dirname(__file__),
        "utilities",
        "swe-bench",
        "SWE-bench_verified.xlsx",
    )

    print(f"\n📊 Organizing instances by repository...")

    # Group by repository
    grouped = df.groupby("repo")
    print(f"✓ Found {len(grouped)} unique repositories")

    # Create Excel writer
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for repo_name, group in grouped:
            # Clean sheet name (Excel has restrictions on sheet names)
            # Replace / with _ and limit to 31 characters
            sheet_name = repo_name.replace("/", "_")
            if len(sheet_name) > 31:
                # Truncate but keep recognizable
                sheet_name = sheet_name[:31]

            # Create DataFrame with only instance_id column
            sheet_df = pd.DataFrame(
                {"instance_id": group["instance_id"]}
            )

            # Write to sheet
            sheet_df.to_excel(
                writer, sheet_name=sheet_name, index=False
            )
            print(
                f"   ✓ {repo_name}: {len(sheet_df)} instances → sheet '{sheet_name}'"
            )

    print(f"\n✅ Excel file created: {output_path}")
    print(f"📄 Total sheets: {len(grouped)}")


if __name__ == "__main__":
    main()
