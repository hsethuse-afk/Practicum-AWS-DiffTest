#!/usr/bin/env python3
"""
Run differential testing from Hugging Face SWE-bench_Verified dataset.

This mode fetches patches directly from the HF dataset and runs differential testing
in the context of the cloned repository to handle relative imports properly.
"""

import argparse
import sys
import os
import pandas as pd
from dt.orchestrator import Orchestrator
from utilities.coverage_runner import handle_coverage


def fetch_dataset_entry(instance_id: str):
    """Fetch a single entry from SWE-bench parquet file by instance ID"""
    # Path to the parquet file
    parquet_path = os.path.join(
        os.path.dirname(__file__),
        "utilities",
        "swe-bench",
        "SWE-bench_verified.parquet",
    )

    if not os.path.exists(parquet_path):
        raise FileNotFoundError(
            f"Parquet file not found at: {parquet_path}"
        )

    print(f"Loading SWE-bench dataset from: {parquet_path}")
    df = pd.read_parquet(parquet_path)

    # Filter by instance_id
    matching_rows = df[df["instance_id"] == instance_id]

    if matching_rows.empty:
        raise ValueError(
            f"Instance ID '{instance_id}' not found in dataset"
        )

    row = matching_rows.iloc[0]

    print(f"✓ Found instance: {instance_id}")
    return {
        "instance_id": row["instance_id"],
        "repo": row["repo"],
        "base_commit": row["base_commit"],
        "patch": row["patch"],
    }


def main():
    p = argparse.ArgumentParser(
        description="Run differential testing from Hugging Face SWE-bench_Verified dataset"
    )

    # Required arguments
    p.add_argument(
        "--instance-id",
        type=str,
        required=True,
        help="Instance ID to fetch from the dataset (e.g., 'django__django-11099')",
    )

    # Optional arguments
    p.add_argument(
        "--func",
        type=str,
        default=None,
        help="Optional: test only this specific function by name",
    )
    p.add_argument(
        "--functions",
        type=str,
        default=None,
        help="Comma-separated function indices to test, e.g., '1,2,3' or '1-3' (optional)",
    )
    p.add_argument(
        "--no-interactive",
        action="store_true",
        help="Skip interactive function selection",
    )
    p.add_argument(
        "--max-examples",
        type=int,
        default=200,
        help="Number of test cases to generate (default: 200)",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible test generation (optional)",
    )
    p.add_argument(
        "--report",
        type=str,
        default=None,
        help="Generate HTML report at specified path (optional)",
    )
    p.add_argument(
        "--log",
        type=str,
        default="N",
        help="Logging mode: (s)ilent, (n)ormal, (v)erbose, (d)ebug",
    )
    p.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report",
    )
    p.add_argument(
        "--no-auto-approve",
        action="store_false",
        dest="auto_approve",
        help="Disable automatic approval of test strategies (requires user confirmation)",
    )
    p.add_argument(
        "--no-install-deps",
        action="store_true",
        help="Skip dependency installation",
    )

    p.set_defaults(auto_approve=True)

    args = p.parse_args()

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

    print(
        f"\n🔬 Running differential testing from SWE-bench_Verified dataset"
    )
    print(f"📊 Dataset: SWE-bench_Verified")
    print(f"📍 Instance ID: {args.instance_id}")
    if args.func:
        print(f"🎯 Testing specific function: {args.func}")
    print()

    try:
        # Fetch entry from parquet file
        entry = fetch_dataset_entry(args.instance_id)

        instance_id = entry["instance_id"]
        repo = entry["repo"]
        base_commit = entry["base_commit"]
        patch_content = entry["patch"]

        if not patch_content or not repo or not base_commit:
            print("❌ Missing required data in dataset entry")
            sys.exit(1)

        print(f"✓ Instance ID: {instance_id}")
        print(f"✓ Repository: {repo}")
        print(f"✓ Base commit: {base_commit[:8]}")
        print(f"✓ Patch size: {len(patch_content)} bytes")
        print()

        # Use orchestrator's run_commit_from_repo method
        # This will handle cloning, virtual env, and running in repo context
        orch = Orchestrator(log_mode=log_mode)

        # Construct repo URL
        repo_url = f"https://github.com/{repo}.git"

        print(f"{'='*60}")
        print(
            f"🧪 Running Differential Tests using Base Commit + Patch"
        )
        print(f"{'='*60}\n")

        # Run differential testing using base commit + patch approach
        # This avoids issues with malformed patch files by:
        # 1. Checking out to base_commit (before state)
        # 2. Applying patch to get after state
        # 3. Comparing the two versions
        results = orch.run_base_and_patch_from_repo(
            repo_url=repo_url,
            base_commit=base_commit,
            patch_content=patch_content,
            func_name=args.func,
            selected_functions=args.functions,
            interactive_select=not args.no_interactive,
            max_examples=args.max_examples,
            auto_approve=args.auto_approve,
            report_path=args.report,
            seed=args.seed,
            install_deps=not args.no_install_deps,
        )

        # Summary
        print(f"\n{'='*60}")
        print(f"📊 Testing Summary")
        print(f"{'='*60}")
        print(f"Total functions tested: {len(results)}")
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        print(f"✅ No Difference Found: {passed}")
        print(f"❌ Differences Found: {failed}")

        if args.report:
            print(f"\n📄 Report saved to: {args.report}")
        print()

    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
