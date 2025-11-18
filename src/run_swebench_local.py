#!/usr/bin/env python3
"""
SWE-bench runner that clones repos locally for full dependency access.

Strategy:
1. Clone repo at base_commit (BEFORE)
2. Apply patch to working directory (AFTER - not as commit)
3. Use file paths directly with Orchestrator.run_pair()

Benefits:
- Full source code locally (browse, debug, set breakpoints)
- All dependencies available (proper package imports)
- Standard HTML report generation
- Perfect for benchmarking with limited test cases
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dt.orchestrator import Orchestrator
from dt.contracts import LoggerMode
from utilities.swebench_integration import PatchParser
from utilities.swebench_integration.test_utils import (
    extract_test_file_from_patch,
)


def clone_repo_at_commit(repo_url: str, commit: str, target_dir: str):
    """Clone repository at specific commit."""
    print(f"\n📥 Cloning repository...")
    print(f"   URL: {repo_url}")
    print(f"   Commit: {commit[:12]}")

    # Clone with depth for speed
    subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, target_dir],
        check=True,
        capture_output=True,
        text=True,
    )

    # Fetch specific commit if needed
    try:
        subprocess.run(
            ["git", "checkout", commit],
            cwd=target_dir,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        print(f"   Fetching commit...")
        subprocess.run(
            ["git", "fetch", "--depth", "100", "origin", commit],
            cwd=target_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "checkout", commit],
            cwd=target_dir,
            check=True,
            capture_output=True,
            text=True,
        )

    print(f"✓ Cloned to: {target_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="SWE-bench runner with local git clones",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python src/run_swebench_local.py --instance-id astropy__astropy-12907 --keep-repo

This will:
  1. Clone the full repository locally
  2. Apply the SWE-bench patch
  3. Run differential testing with all dependencies available
  4. Generate HTML report in reports/
        """,
    )

    parser.add_argument(
        "--instance-id", required=True, help="SWE-bench instance ID"
    )
    parser.add_argument(
        "--dataset",
        default="princeton-nlp/SWE-bench_Verified",
        help="Dataset name",
    )
    parser.add_argument(
        "--max-examples",
        type=int,
        default=200,
        help="Max test examples",
    )
    parser.add_argument("--seed", type=int, help="Random seed")
    parser.add_argument(
        "--verbose", action="store_true", help="Verbose output"
    )
    parser.add_argument(
        "--keep-repo",
        action="store_true",
        help="Keep cloned repo for debugging",
    )
    parser.add_argument(
        "--work-dir", help="Work directory (default: temp)"
    )

    args = parser.parse_args()

    # Load SWE-bench instance
    try:
        from swebench.harness.utils import load_swebench_dataset
    except ImportError:
        print(
            "\n❌ Install SWE-bench: pip install -e git+https://github.com/princeton-nlp/SWE-bench.git"
        )
        sys.exit(1)

    print(f"\n{'='*80}")
    print(f"🔬 SWE-bench Local Mode: {args.instance_id}")
    print(f"{'='*80}")

    # Load instance
    print("\n📚 Loading instance...")
    dataset = load_swebench_dataset(
        name=args.dataset,
        split="test",
        instance_ids=[args.instance_id],
    )

    if not dataset:
        print(f"❌ Instance not found: {args.instance_id}")
        sys.exit(1)

    instance = dataset[0]
    repo_name = instance["repo"]
    base_commit = instance["base_commit"]
    patch = instance["patch"]

    print(f"✓ Repository: {repo_name}")
    print(f"  Base commit: {base_commit[:12]}")

    # Setup work directory
    if args.work_dir is None:
        # Default to swebench_workspace in the project root
        script_dir = Path(__file__).parent.parent
        work_dir = os.path.join(script_dir, "swebench_workspace", args.instance_id)
    else:
        work_dir = args.work_dir

    os.makedirs(work_dir, exist_ok=True)

    try:
        # Clone repo at base_commit - we need TWO copies
        repo_url = f"https://github.com/{repo_name}.git"
        before_repo = os.path.join(
            work_dir, "before", repo_name.split("/")[-1]
        )
        after_repo = os.path.join(
            work_dir, "after", repo_name.split("/")[-1]
        )

        # Clone BEFORE version
        clone_repo_at_commit(repo_url, base_commit, before_repo)

        # Clone AFTER version (copy from before, then apply patch)
        print(f"\n📋 Creating AFTER version...")
        shutil.copytree(before_repo, after_repo)
        print(f"✓ Copied to: {after_repo}")

        # Parse patch to find target file and function
        parser = PatchParser()
        python_files = parser.extract_python_files(patch)

        if not python_files:
            print("❌ No Python files in patch")
            sys.exit(1)

        target_file = python_files[0]
        func_name = parser.get_primary_function(patch)

        print(f"\n🎯 Target:")
        print(f"   File: {target_file}")
        print(f"   Function: {func_name}")

        # Get file paths
        before_file = os.path.join(before_repo, target_file)
        after_file = os.path.join(after_repo, target_file)

        if not os.path.exists(before_file):
            print(f"❌ File not found: {before_file}")
            sys.exit(1)

        # Apply patch to AFTER version
        print(f"\n🔧 Applying patch to AFTER version...")
        patch_file = os.path.abspath(
            os.path.join(work_dir, "patch.diff")
        )
        with open(patch_file, "w") as f:
            f.write(patch)

        try:
            subprocess.run(
                ["git", "apply", patch_file],
                cwd=after_repo,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError:
            # Try with patch command
            subprocess.run(
                ["patch", "-p1", "-i", patch_file],
                cwd=after_repo,
                check=True,
            )

        print(f"✓ Patch applied to AFTER version")

        # Extract test file for RightTyper
        test_file = None
        if instance.get("test_patch"):
            print(f"\n📝 Extracting test file...")
            test_file = os.path.join(work_dir, "test_context.py")
            test_file = extract_test_file_from_patch(
                instance["test_patch"], test_file
            )
            if test_file:
                print(f"✓ Test file ready")

        # Run differential testing
        print(f"\n{'='*80}")
        print("🔬 Running Differential Testing")
        print(f"{'='*80}\n")

        log_mode = (
            LoggerMode.Verbose if args.verbose else LoggerMode.Normal
        )
        orchestrator = Orchestrator(log_mode=log_mode)

        report_path = f"reports/{args.instance_id}.html"
        os.makedirs("reports", exist_ok=True)

        orchestrator.run_pair(
            file_a=before_file,  # BEFORE state
            file_b=after_file,  # AFTER state (with patch)
            func_name=func_name,
            max_examples=args.max_examples,
            test_file=test_file,
            auto_approve=True,
            report_path=report_path,
            seed=args.seed,
        )

        # Success!
        print(f"\n{'='*80}")
        print("✅ Testing Complete!")
        print(f"{'='*80}")
        print(f"📊 Report: {report_path}")

        print(f"\n📁 Repositories:")
        print(f"   BEFORE: {before_repo}")
        print(f"   AFTER:  {after_repo}")
        print(f"   Work dir: {work_dir}")
        print("   Browse source, debug, set breakpoints!")

    finally:
        if not args.keep_repo:
            print(f"\n🗑️  Cleaning up: {work_dir}")
            shutil.rmtree(work_dir, ignore_errors=True)
        else:
            print(f"\n✓ Repository kept: {work_dir}")

    sys.exit(0)


if __name__ == "__main__":
    main()
