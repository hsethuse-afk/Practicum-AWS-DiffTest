#!/usr/bin/env python3
"""
Run differential testing from a git diff with repository context.

This is the main entry point when you ONLY have:
- A git diff file
- A repository URL

The tool will:
1. Clone the repository
2. Install dependencies
3. Extract modified functions from the diff
4. Run differential tests with full type inference
"""

import argparse
from dt.orchestrator import Orchestrator
from utilities.coverage_runner import handle_coverage


def main():
    p = argparse.ArgumentParser(
        description="Run differential testing from git diff with repository context"
    )

    # Required arguments
    p.add_argument(
        "--diff",
        type=str,
        required=True,
        help="Path to git diff file"
    )
    p.add_argument(
        "--repo",
        type=str,
        required=True,
        help="Repository URL (e.g., https://github.com/user/repo.git)"
    )

    # Optional arguments
    p.add_argument(
        "--commit",
        type=str,
        default=None,
        help="Specific commit hash (auto-detected from diff if not provided)"
    )
    p.add_argument(
        "--func",
        type=str,
        default=None,
        help="Optional: test only this specific function"
    )
    p.add_argument(
        "--max-examples",
        type=int,
        default=200,
        help="Number of test cases to generate (default: 200)"
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

    # Run differential testing with repository context
    print(f"\n🔬 Running differential testing from diff...")
    print(f"📁 Diff file: {args.diff}")
    print(f"🌐 Repository: {args.repo}")
    print(f"📦 Install deps: {not args.no_install_deps}")
    print()

    results = orch.run_diff_with_repo(
        diff_file_path=args.diff,
        repo_url=args.repo,
        commit=args.commit,
        func_name=args.func,
        max_examples=args.max_examples,
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
    print()


if __name__ == "__main__":
    main()
