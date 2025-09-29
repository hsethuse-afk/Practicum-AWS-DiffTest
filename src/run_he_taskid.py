#!/usr/bin/env python3
import argparse
import os
import sys
import subprocess
from dt.orchestrator import Orchestrator
from utilities.extractor import extract_task, extract_entry


def main():
    p = argparse.ArgumentParser(
        description="Run A/B differential test based on human-eval task id."
    )
    p.add_argument("--t", required=True, help="Human-eval task id")

    p.add_argument("--max-examples", type=int, default=200)

    p.add_argument("--log", type=str, default="N")
    p.add_argument("--coverage", action="store_true", help="Generate coverage report for the two generated files.")

    args = p.parse_args()

    val = args.log.lower()
    log_mode = 2

    if val in ("s", "silent"):
        log_mode = 1
    elif val in ("v", "verbose"):
        log_mode = 3
    elif val in ("d", "debug"):
        log_mode = 4
    # extract task
    OUT_PATH = "./testsample/"
    ORIGINAL_JSON = "./utilities/human_eval/human_eval.jsonl"
    COMPLETION_JSON = (
        "./utilities/human_eval/human_eval_completion.jsonl"
    )
    canonical_path = extract_task(
        ORIGINAL_JSON,
        args.t,
        OUT_PATH + "a.py",
    )
    completion_path = extract_task(
        COMPLETION_JSON,
        args.t,
        OUT_PATH + "b.py",
    )
    if log_mode > 1:
        print(
            f"Canonical Solution saved to: {canonical_path}, GPT Solution saved to {completion_path}"
        )

    # If coverage is requested, re-run the script under slipcover and exit.
    # This is done *after* the source files are created.
    if args.coverage:
        if "SLIPCOVER_RUNNING" in os.environ:
            # We are in the child process, proceed with the test run.
            pass
        else:
            print("Running with Slipcover for code coverage on target files...")
            source_dir = os.path.dirname(canonical_path) or "."
            cmd = [
                sys.executable, "-m", "slipcover",
                "--source", source_dir,
                *sys.argv
            ]
            env = os.environ.copy()
            env["SLIPCOVER_RUNNING"] = "1"
            result = subprocess.run(cmd, env=env)
            # After the coverage run, the parent process can exit.
            sys.exit(result.returncode)

    function_name = extract_entry(ORIGINAL_JSON, args.t)
    orch = Orchestrator(log_mode=log_mode)
    orch.run_pair(
        canonical_path,
        completion_path,
        function_name,
        max_examples=args.max_examples,
    )


if __name__ == "__main__":
    main()
