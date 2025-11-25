#!/usr/bin/env python3
"""
Run differential testing from a patch file without git commit context.

This mode reconstructs the old and new file versions directly from the patch,
making it useful when you have a patch file but no access to the git repository.
"""

import argparse
from dt.orchestrator import Orchestrator
from utilities.coverage_runner import handle_coverage


def main():
    p = argparse.ArgumentParser(
        description="Run differential testing from a patch file (no git commit needed)"
    )

    # Required arguments
    p.add_argument(
        "--patch",
        type=str,
        required=True,
        help="Path to patch/diff file"
    )

    # Optional arguments
    p.add_argument(
        "--func",
        type=str,
        default=None,
        help="Optional: test only this specific function by name"
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
        help="Generate coverage report.",
    )
    p.add_argument(
        "--auto-approve",
        action="store_true",
        help="Automatically approve test strategies without user confirmation"
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

    # Create orchestrator
    orch = Orchestrator(log_mode=log_mode)

    # Run differential testing from patch
    print(f"\n🔬 Running differential testing from patch file...")
    print(f"📄 Patch: {args.patch}")
    if args.func:
        print(f"🎯 Testing specific function: {args.func}")
    print()

    results = orch.run_patch_file(
        patch_file_path=args.patch,
        func_name=args.func,
        max_examples=args.max_examples,
        auto_approve=args.auto_approve,
        report_path=args.report,
        seed=args.seed,
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
    print()


if __name__ == "__main__":
    main()
