#!/usr/bin/env python3
"""
Run differential testing directly from a commit in a remote repository.

This is simpler than run_diff_repo - just provide repo URL and commit!
No need to create a diff file first.
"""

import argparse
from dt.orchestrator import Orchestrator
from utilities.coverage_runner import handle_coverage


def main():
    p = argparse.ArgumentParser(
        description="Run differential testing directly from a commit"
    )

    # Required arguments
    p.add_argument(
        "--repo",
        type=str,
        required=True,
        help="Repository URL (e.g., https://github.com/user/repo.git)"
    )
    p.add_argument(
        "--commit",
        type=str,
        required=True,
        help="Commit hash to test (e.g., ed7facc1b108ceff12bcb412d7a98471509f41b0)"
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
        help="Optional: comma-separated function indices to test (e.g., '1,2,3' or '1-3'). Use with --no-interactive to skip selection prompt."
    )
    p.add_argument(
        "--no-interactive",
        action="store_true",
        help="Skip interactive function selection. If --functions not specified, tests all functions."
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
        "--no-install-deps",
        action="store_true",
        help="Skip installing dependencies from requirements.txt"
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

    # Run differential testing from commit
    print(f"\n🔬 Running differential testing from commit...")
    print(f"🌐 Repository: {args.repo}")
    print(f"📌 Commit: {args.commit}")
    print(f"📦 Install deps: {not args.no_install_deps}")
    print()

    results = orch.run_commit_from_repo(
        repo_url=args.repo,
        commit=args.commit,
        func_name=args.func,
        max_examples=args.max_examples,
        install_deps=not args.no_install_deps,
        interactive_select=not args.no_interactive,
        selected_functions=args.functions,
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
