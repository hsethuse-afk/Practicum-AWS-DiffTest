#!/usr/bin/env python3
import argparse
import os
import json
import multiprocessing
from dt.orchestrator import Orchestrator
from utilities.extractor import (
    extract_task,
    extract_entry,
    extract_test,
)
from utilities.coverage_runner import handle_coverage


def run_single_test(
    task_id,
    max_examples,
    log_mode,
    test_coverage,
    out_path,
    original_json,
    completion_json,
    timeout=None,
):
    """Run a single test case and return the result summary."""
    # Extract task
    canonical_path = extract_task(
        original_json,
        task_id,
        out_path + "a.py",
    )
    completion_path = extract_task(
        completion_json,
        task_id,
        out_path + "b.py",
    )
    # Extract test files
    test_path = extract_test(
        original_json, task_id, out_path + "test.py"
    )

    if log_mode > 1:
        print(
            f"Canonical Solution saved to: {canonical_path}, GPT Solution saved to {completion_path}"
        )

    # If coverage is requested, re-run the script under slipcover
    if test_coverage:
        source_dir = os.path.dirname(canonical_path) or "."
        handle_coverage(source_dir)

    function_name = extract_entry(original_json, task_id)
    orch = Orchestrator(log_mode=log_mode, timeout=timeout)
    result = orch.run_pair(
        canonical_path,
        completion_path,
        function_name,
        auto_approve=True,
        max_examples=max_examples,
        test_file=test_path,
        timeout=timeout,
    )

    # Get simple difference summary
    diff_summary = orch.get_difference(result) if result else None

    return {
        "task_id": task_id,
        "function_name": function_name,
        "tool_result": diff_summary,
        "timed_out": result is None,
    }


def load_dataset_expectations(json_path):
    """Load the human-eval dataset and extract expected results."""
    expectations = {}
    with open(json_path, "r") as f:
        for line in f:
            data = json.loads(line.strip())
            task_id = data.get("task_id", "")
            # For now, assume canonical solutions should have no difference
            # and completion solutions may have differences
            expectations[task_id] = {
                "expected_difference": False,  # Canonical vs completion comparison
            }
    return expectations


def _run_test_in_process(args):
    """Wrapper function for multiprocessing - must be at module level for pickling."""
    (
        task_id,
        max_examples,
        log_mode,
        out_path,
        original_json,
        completion_json,
        timeout,
    ) = args
    try:
        result = run_single_test(
            task_id=task_id,
            max_examples=max_examples,
            log_mode=log_mode,
            test_coverage=False,
            out_path=out_path,
            original_json=original_json,
            completion_json=completion_json,
            timeout=timeout,
        )
        return ("success", result)
    except Exception as e:
        import traceback

        return ("error", str(e), traceback.format_exc())


def run_all_tests(
    max_examples,
    log_mode,
    out_path,
    original_json,
    completion_json,
    dataset_path=None,
    timeout=5,
):
    """
    Run all tests in the human-eval dataset and generate a report.

    Args:
        timeout: Timeout in seconds for each test (default: 5s)
    """
    print("\n" + "=" * 80)
    print("RUNNING BATCH BENCHMARKING FOR HUMAN-EVAL DATASET")
    print(f"⏱️  Timeout: {timeout}s per test")
    print("=" * 80 + "\n")

    # Load dataset expectations if provided
    expectations = {}
    if dataset_path:
        try:
            expectations = load_dataset_expectations(dataset_path)
            print(
                f"✓ Loaded expectations for {len(expectations)} tasks from dataset\n"
            )
        except Exception as e:
            print(
                f"⚠ Warning: Could not load dataset expectations: {e}\n"
            )

    # Get all task IDs from the dataset
    task_ids = []
    with open(original_json, "r") as f:
        for line in f:
            data = json.loads(line.strip())
            task_id = data.get("task_id", "")
            if task_id:
                task_ids.append(task_id)

    print(f"Found {len(task_ids)} tasks to test\n")

    # Run all tests
    results = []
    passed = 0
    failed = 0

    # Prepare all test arguments
    all_test_args = [
        (
            task_id,
            max_examples,
            log_mode,
            out_path,
            original_json,
            completion_json,
            timeout,
        )
        for task_id in task_ids
    ]

    # Run tests sequentially or in parallel
    for i, (task_id, args) in enumerate(
        zip(task_ids, all_test_args), 1
    ):
        print(f"\n[{i}/{len(task_ids)}] Testing {task_id}...")
        print("-" * 60)

        try:
            # Run test in a separate process with timeout
            with multiprocessing.Pool(processes=1) as pool:
                async_result = pool.apply_async(
                    _run_test_in_process, (args,)
                )

                try:
                    # Wait for result with timeout
                    test_result = async_result.get(timeout=timeout + 2)
                    status = test_result[0]

                    if status == "error":
                        error_msg = test_result[1]
                        print(f"✗ ERROR: {error_msg}")
                        failed += 1
                        results.append(
                            {
                                "task_id": task_id,
                                "function_name": "unknown",
                                "tool_result": None,
                                "expected_difference": None,
                                "validation_passed": False,
                                "error": error_msg,
                            }
                        )
                    else:
                        result = test_result[1]

                        # Check if test timed out internally
                        if result.get("timed_out", False):
                            failed += 1
                            result["expected_difference"] = None
                            result["validation_passed"] = False
                            result["error"] = (
                                f"Timeout after {timeout}s"
                            )
                            results.append(result)
                            print(
                                f"✗ TIMEOUT: Test exceeded {timeout}s"
                            )
                        else:
                            # Validate against dataset expectations
                            tool_says_diff = result["tool_result"][
                                "difference_found"
                            ]
                            expected = expectations.get(task_id, {})
                            expected_diff = expected.get(
                                "expected_difference", False
                            )

                            # Determine if test passed validation
                            validation_passed = (
                                tool_says_diff == expected_diff
                            )

                            result["expected_difference"] = (
                                expected_diff
                            )
                            result["validation_passed"] = (
                                validation_passed
                            )

                            if validation_passed:
                                passed += 1
                                status_str = "✓ PASS"
                            else:
                                failed += 1
                                status_str = "✗ FAIL"

                            results.append(result)
                            print(
                                f"{status_str}: Tool={tool_says_diff}, Expected={expected_diff}"
                            )

                except multiprocessing.TimeoutError:
                    # Process timed out - terminate the pool
                    pool.terminate()
                    pool.join()

                    failed += 1
                    result = {
                        "task_id": task_id,
                        "function_name": "unknown",
                        "tool_result": None,
                        "expected_difference": None,
                        "validation_passed": False,
                        "error": f"Timeout after {timeout}s",
                        "timed_out": True,
                    }
                    results.append(result)
                    print(f"✗ TIMEOUT: Test exceeded {timeout}s")

        except Exception as e:
            print(f"✗ ERROR: {e}")
            failed += 1
            results.append(
                {
                    "task_id": task_id,
                    "function_name": "unknown",
                    "tool_result": None,
                    "expected_difference": None,
                    "validation_passed": False,
                    "error": str(e),
                }
            )

    # Save results to file
    import datetime

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"human-eval_benchmark_results_{timestamp}.json"

    with open(results_file, "w") as f:
        json.dump(
            {
                "timestamp": timestamp,
                "total_tests": len(task_ids),
                "passed": passed,
                "failed": failed,
                "success_rate": passed / len(task_ids) * 100,
                "timeout": timeout,
                "max_examples": max_examples,
                "results": results,
            },
            f,
            indent=2,
        )

    print(f"\n✓ Results saved to: {results_file}")

    # Build summary report (print at the very end)
    summary_lines = []
    summary_lines.append("=" * 80)
    summary_lines.append("DETAILED RESULTS")
    summary_lines.append("=" * 80)

    for result in results:
        task_id = result["task_id"]
        func_name = result["function_name"]
        status = "✓" if result.get("validation_passed", False) else "✗"

        if result.get("error"):
            summary_lines.append(f"\n{status} {task_id} ({func_name})")
            summary_lines.append(f"   ERROR: {result['error']}")
        else:
            tool_result = result["tool_result"]
            expected = result.get("expected_difference", "N/A")
            tool_diff = (
                tool_result["difference_found"]
                if tool_result
                else "N/A"
            )

            summary_lines.append(f"\n{status} {task_id} ({func_name})")
            summary_lines.append(
                f"   Tool result: {'Difference found' if tool_diff else 'No difference'}"
            )
            summary_lines.append(
                f"   Expected: {'Difference' if expected else 'No difference'}"
            )

            if tool_result:
                summary_lines.append(
                    f"   Total examples: {tool_result['total_examples']}"
                )
                summary_lines.append(
                    f"   Mismatches: {tool_result['mismatches']}"
                )
                if tool_result.get("reason"):
                    summary_lines.append(
                        f"   Reason: {tool_result['reason']}"
                    )

    summary_lines.append("\n" + "=" * 80 + "\n")
    summary_lines.append("\n" + "=" * 80)
    summary_lines.append("BENCHMARKING SUMMARY")
    summary_lines.append("=" * 80)
    summary_lines.append(f"Total test cases: {len(task_ids)}")
    summary_lines.append(f"✓ Passed: {passed}")
    summary_lines.append(f"✗ Failed: {failed}")
    summary_lines.append(
        f"Success rate: {passed/len(task_ids)*100:.1f}%"
    )
    summary_lines.append("")

    # Print everything at once to avoid interleaving with other output
    print("\n".join(summary_lines))

    return results


def main():
    p = argparse.ArgumentParser(
        description="Run A/B differential test based on human-eval task id."
    )
    p.add_argument(
        "--t", help="Human-eval task id (omit for --run-all mode)"
    )
    p.add_argument(
        "--run-all",
        action="store_true",
        help="Run all tests in the human-eval dataset",
    )
    p.add_argument("--max-examples", type=int, default=200)
    p.add_argument("--log", type=str, default="N")
    p.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report for the two generated files.",
    )
    p.add_argument(
        "--dataset",
        type=str,
        help="Path to dataset file for validation (optional)",
    )
    p.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="Timeout in seconds for each test (default: 5s, only applies to --run-all)",
    )

    args = p.parse_args()

    # Validate arguments
    if not args.run_all and not args.t:
        p.error("Either --t or --run-all must be specified")
    if args.run_all and args.t:
        p.error("Cannot specify both --t and --run-all")

    val = args.log.lower()
    log_mode = 2

    if val in ("s", "silent"):
        log_mode = 1
    elif val in ("v", "verbose"):
        log_mode = 3
    elif val in ("d", "debug"):
        log_mode = 4

    # Define paths
    OUT_PATH = "./testsample/"
    ORIGINAL_JSON = "./src/utilities/human_eval/human_eval.jsonl"
    COMPLETION_JSON = (
        "./src/utilities/human_eval/human_eval_completion.jsonl"
    )

    # Run all tests or single test
    if args.run_all:
        dataset_path = args.dataset if args.dataset else ORIGINAL_JSON
        run_all_tests(
            max_examples=args.max_examples,
            log_mode=log_mode,
            out_path=OUT_PATH,
            original_json=ORIGINAL_JSON,
            completion_json=COMPLETION_JSON,
            dataset_path=dataset_path,
            timeout=args.timeout,
        )
    else:
        # Single test mode (original behavior)
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
        # extract test files
        test_path = extract_test(
            ORIGINAL_JSON, args.t, OUT_PATH + "test.py"
        )
        if log_mode > 1:
            print(
                f"Canonical Solution saved to: {canonical_path}, GPT Solution saved to {completion_path}"
            )

        # If coverage is requested, re-run the script under slipcover
        if args.coverage:
            source_dir = os.path.dirname(canonical_path) or "."
            handle_coverage(source_dir)

        function_name = extract_entry(ORIGINAL_JSON, args.t)
        orch = Orchestrator(log_mode=log_mode)
        result = orch.run_pair(
            canonical_path,
            completion_path,
            function_name,
            auto_approve=True,
            max_examples=args.max_examples,
            test_file=test_path,
        )

        # Print simple result summary
        diff_summary = orch.get_difference(result)
        if diff_summary:
            print("\n" + "=" * 60)
            print("RESULT SUMMARY:")
            print(
                f"  Difference found: {diff_summary['difference_found']}"
            )
            print(f"  Total examples: {diff_summary['total_examples']}")
            print(f"  Mismatches: {diff_summary['mismatches']}")
            if diff_summary["reason"]:
                print(f"  Reason: {diff_summary['reason']}")
            print("=" * 60)


if __name__ == "__main__":
    main()
