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
    args = p.parse_args()

    orch = Orchestrator()
    orch.run_pair(
        args.a, args.b, args.func, max_examples=args.max_examples
    )


if __name__ == "__main__":
    main()
