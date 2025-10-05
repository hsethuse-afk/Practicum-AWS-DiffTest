#!/usr/bin/env python3
import argparse
from dt.orchestrator import Orchestrator


def main():
    p = argparse.ArgumentParser(
        description="Run A/B differential test on two files for one function."
    )
    p.add_argument(
        "--a", required=True, help="Path to file A (reference)"
    )
    p.add_argument(
        "--b", required=True, help="Path to file B (candidate)"
    )
    p.add_argument(
        "--func", required=True, help="Function name (entrypoint)"
    )
    p.add_argument("--max-examples", type=int, default=200)
    p.add_argument("--log", type=str, default="N")
    p.add_argument(
        "--test-file",
        type=str,
        default=None,
        help="Optional path to test file for type inference (e.g., 'test.py')",
    )
    args = p.parse_args()

    val = args.log.lower()
    log_mode = 2

    if val in ("s", "silent"):
        log_mode = 1
    elif val in ("v", "verbose"):
        log_mode = 3
    elif val in ("d", "debug"):
        log_mode = 4

    orch = Orchestrator(log_mode=log_mode)
    orch.run_pair(
        args.a,
        args.b,
        args.func,
        max_examples=args.max_examples,
        test_file=args.test_file,
    )


if __name__ == "__main__":
    main()
