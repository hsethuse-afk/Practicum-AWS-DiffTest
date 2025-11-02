#!/usr/bin/env python3
import argparse
import os
from dt.orchestrator import Orchestrator
from utilities.coverage_runner import handle_coverage


def main():
    p = argparse.ArgumentParser(
        description="Run A/B differential test on two files for one function, or on git diff."
    )

    # Mode selection: manual files or git diff
    mode_group = p.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--a",
        type=str,
        help="Path to file A (reference) - use with --b and --func"
    )
    mode_group.add_argument(
        "--commit",
        type=str,
        help="Git commit to analyze (e.g., HEAD, abc123, HEAD~1)"
    )
    mode_group.add_argument(
        "--diff-file",
        type=str,
        help="Path to file containing git diff output"
    )

    # Required for manual mode
    p.add_argument(
        "--b",
        type=str,
        help="Path to file B (candidate) - required with --a"
    )
    p.add_argument(
        "--func",
        type=str,
        help="Function name (entrypoint) - required with --a, optional with git diff mode"
    )

    # Common options
    p.add_argument("--max-examples", type=int, default=200)
    p.add_argument("--log", type=str, default="N")
    p.add_argument(
        "--test-file",
        type=str,
        default=None,
        help="Optional path to test file for type inference (e.g., 'test.py')",
    )
    p.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report.",
    )
    args = p.parse_args()

    # Handle coverage
    if args.a:
        source_dir = os.path.dirname(args.a) or "."
        handle_coverage(source_dir)

    # Validate arguments based on mode
    if args.a:
        # Manual mode
        if not args.b or not args.func:
            p.error("--a requires --b and --func")
    elif args.commit or args.diff_file:
        # Git diff mode - func is optional
        pass

    val = args.log.lower()
    log_mode = 2

    if val in ("s", "silent"):
        log_mode = 1
    elif val in ("v", "verbose"):
        log_mode = 3
    elif val in ("d", "debug"):
        log_mode = 4

    orch = Orchestrator(log_mode=log_mode)

    # Execute based on mode
    if args.a:
        # Manual mode: test specific file pair
        orch.run_pair(
            args.a,
            args.b,
            args.func,
            max_examples=args.max_examples,
            test_file=args.test_file,
        )
    elif args.commit:
        # Git commit mode
        orch.run_git_diff(
            commit=args.commit,
            func_name=args.func,
            max_examples=args.max_examples,
            test_file=args.test_file,
        )
    elif args.diff_file:
        # Diff file mode
        orch.run_diff_file(
            diff_file_path=args.diff_file,
            func_name=args.func,
            max_examples=args.max_examples,
            test_file=args.test_file,
        )


if __name__ == "__main__":
    main()
