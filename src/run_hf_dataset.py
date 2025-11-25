#!/usr/bin/env python3
"""
Run differential testing from Hugging Face SWE-bench_Verified dataset.

This mode fetches patches directly from the HF dataset and runs differential testing
in the context of the cloned repository to handle relative imports properly.
"""

import argparse
import sys
import requests
from dt.orchestrator import Orchestrator
from utilities.coverage_runner import handle_coverage


def fetch_hf_dataset_entry(dataset_index: int):
    """Fetch a single entry from HF dataset"""
    url = "https://datasets-server.huggingface.co/rows"
    params = {
        "dataset": "princeton-nlp/SWE-bench_Verified",
        "config": "default",
        "split": "test",
        "offset": 0,
        "length": 100
    }

    print(f"Fetching data from Hugging Face dataset...")
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    rows = data.get('rows', [])
    if not rows or dataset_index >= len(rows):
        raise ValueError(f"Invalid index {dataset_index}")

    row = rows[dataset_index]['row']
    return {
        'instance_id': row.get('instance_id', f'index_{dataset_index}'),
        'repo': row.get('repo', ''),
        'base_commit': row.get('base_commit', ''),
        'patch': row.get('patch', '')
    }


def main():
    p = argparse.ArgumentParser(
        description="Run differential testing from Hugging Face SWE-bench_Verified dataset"
    )

    # Required arguments
    p.add_argument(
        "--index",
        type=int,
        required=True,
        help="Dataset index to fetch (0-99 for first 100 entries)"
    )

    # Optional arguments
    p.add_argument(
        "--func",
        type=str,
        default=None,
        help="Optional: test only this specific function by name"
    )
    p.add_argument(
        "--functions",
        type=str,
        default=None,
        help="Comma-separated function indices to test, e.g., '1,2,3' or '1-3' (optional)"
    )
    p.add_argument(
        "--no-interactive",
        action="store_true",
        help="Skip interactive function selection"
    )
    p.add_argument(
        "--max-examples",
        type=int,
        default=200,
        help="Number of test cases to generate (default: 200)"
    )
    p.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible test generation (optional)"
    )
    p.add_argument(
        "--report",
        type=str,
        default=None,
        help="Generate HTML report at specified path (optional)"
    )
    p.add_argument(
        "--log",
        type=str,
        default="N",
        help="Logging mode: (s)ilent, (n)ormal, (v)erbose, (d)ebug"
    )
    p.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    p.add_argument(
        "--auto-approve",
        action="store_true",
        help="Automatically approve test strategies without user confirmation"
    )
    p.add_argument(
        "--no-install-deps",
        action="store_true",
        help="Skip dependency installation"
    )

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

    print(f"\n🔬 Running differential testing from HuggingFace dataset")
    print(f"📊 Dataset: SWE-bench_Verified")
    print(f"📍 Index: {args.index}")
    if args.func:
        print(f"🎯 Testing specific function: {args.func}")
    print()

    try:
        # Fetch entry from HF dataset
        entry = fetch_hf_dataset_entry(args.index)

        instance_id = entry['instance_id']
        repo = entry['repo']
        base_commit = entry['base_commit']
        patch_content = entry['patch']

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
        print(f"🧪 Running Differential Tests using Base Commit + Patch")
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
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")

        if args.report:
            print(f"\n📄 Report saved to: {args.report}")
        print()

    except requests.RequestException as e:
        print(f"❌ Failed to fetch data from Hugging Face: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
