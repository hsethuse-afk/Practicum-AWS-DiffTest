#!/usr/bin/env python3
"""
SWE-bench runner that executes differential testing INSIDE Docker containers.

Strategy:
1. Use SWE-bench's Docker images (already built with all dependencies)
2. Copy orchestrator code INTO the container
3. Run differential testing INSIDE the container
4. Extract HTML report OUT of the container

Benefits:
- All imports work (full build environment)
- No local build required
- Leverages SWE-bench infrastructure
- Clean separation: one container per test
"""

import argparse
import os
import sys
import tempfile
import tarfile
from pathlib import Path
from io import BytesIO

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utilities.swebench_integration import PatchParser
from utilities.swebench_integration.test_utils import (
    extract_test_file_from_patch,
)


def copy_directory_to_container(
    container, local_path: str, container_path: str
):
    """Copy a directory into a Docker container using tar."""
    print(f"   Copying {local_path} -> {container_path}")

    # Create tar archive in memory
    tar_stream = BytesIO()
    with tarfile.open(fileobj=tar_stream, mode="w") as tar:
        tar.add(local_path, arcname=os.path.basename(container_path))

    tar_stream.seek(0)

    # Extract to container (extract to parent directory)
    parent_dir = os.path.dirname(container_path)
    if not parent_dir or parent_dir == "/":
        parent_dir = "/"

    container.put_archive(path=parent_dir, data=tar_stream)


def copy_file_to_container(
    container, local_path: str, container_path: str
):
    """Copy a single file into a Docker container."""
    print(f"   Copying {local_path} -> {container_path}")

    # Create tar archive in memory with the file
    tar_stream = BytesIO()
    with tarfile.open(fileobj=tar_stream, mode="w") as tar:
        tar.add(local_path, arcname=os.path.basename(container_path))

    tar_stream.seek(0)

    # Extract to container
    container.put_archive(
        path=os.path.dirname(container_path), data=tar_stream
    )


def extract_file_from_container(
    container, container_path: str, local_path: str
):
    """Extract a file from a Docker container."""
    print(f"   Extracting {container_path} -> {local_path}")

    # Get tar stream from container
    bits, stat = container.get_archive(container_path)

    # Write to local file
    tar_stream = BytesIO()
    for chunk in bits:
        tar_stream.write(chunk)
    tar_stream.seek(0)

    # Extract from tar
    with tarfile.open(fileobj=tar_stream, mode="r") as tar:
        member = tar.getmembers()[0]
        file_obj = tar.extractfile(member)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(file_obj.read())


def create_test_runner_script(
    target_file: str,
    func_name: str,
    max_examples: int,
    seed: int,
    test_file_path: str = None,
) -> str:
    """Generate a Python script to run inside the container using git states."""

    seed_arg = f", seed={seed}" if seed else ""
    test_file_arg = (
        f', test_file="{test_file_path}"'
        if test_file_path
        else ", test_file=None"
    )

    script = f'''#!/usr/bin/env python3
"""Auto-generated differential testing script - uses git to manage states."""

import sys
import os
import subprocess

# Add dt package to path
sys.path.insert(0, '/tmp')
# Add testbed to path so we can import packages
sys.path.insert(0, '/testbed')

from dt.orchestrator import Orchestrator
from dt.contracts import LoggerMode

def main():
    print("="*80)
    print("🔬 Running Differential Testing Inside Container")
    print("="*80)

    target_file = "{target_file}"

    try:
        # Step 1: Extract BEFORE version using git and save next to AFTER
        print(f"\\n📥 Extracting BEFORE version using git...")

        # Create a temporary .before version of the file in the same directory
        target_path = os.path.join("/testbed", target_file)
        before_file = target_path.replace(".py", "_before.py")

        # Use git show to get file at base commit (before patch)
        result = subprocess.run(
            ["git", "show", "HEAD~1:{{}}".format(target_file)],
            cwd="/testbed",
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            # Try current HEAD (if patch was applied as commit)
            result = subprocess.run(
                ["git", "show", "HEAD^:{{}}".format(target_file)],
                cwd="/testbed",
                capture_output=True,
                text=True
            )

        if result.returncode != 0:
            print(f"❌ Could not extract BEFORE version from git")
            print(f"   Error: {{result.stderr}}")
            sys.exit(1)

        # Write BEFORE version next to the AFTER version (same package context)
        with open(before_file, 'w') as f:
            f.write(result.stdout)

        print(f"✓ BEFORE: {{before_file}}")

        # Step 2: AFTER version is current /testbed
        after_file = target_path

        if not os.path.exists(after_file):
            print(f"❌ AFTER file not found: {{after_file}}")
            sys.exit(1)

        print(f"✓ AFTER: {{after_file}}")

        # Step 3: Run differential testing
        print("\\n" + "="*80)
        print("🧪 Executing Differential Tests")
        print("="*80 + "\\n")

        orchestrator = Orchestrator(log_mode=LoggerMode.Normal)

        orchestrator.run_pair(
            file_a=before_file,
            file_b=after_file,
            func_name="{func_name}",
            max_examples={max_examples},
            auto_approve=True,
            report_path="/tmp/report.html"{test_file_arg}{seed_arg}
        )

        print("\\n" + "="*80)
        print("✅ Differential Testing Complete!")
        print("="*80)
        print("📊 Report: /tmp/report.html")

    except Exception as e:
        print(f"\\n❌ Error during testing: {{e}}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        # Cleanup temporary before file
        if os.path.exists(before_file):
            os.remove(before_file)

if __name__ == "__main__":
    main()
'''

    return script


def main():
    parser = argparse.ArgumentParser(
        description="SWE-bench runner with in-container differential testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python src/run_swebench_docker.py --instance-id astropy__astropy-12907 --max-examples 50

This will:
  1. Start SWE-bench Docker container (already built environment)
  2. Copy orchestrator code INTO the container
  3. Create BEFORE state backup
  4. Apply patch for AFTER state
  5. Run differential testing INSIDE container (all imports work!)
  6. Extract HTML report
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
        "--keep-container",
        action="store_true",
        help="Keep container for debugging",
    )

    args = parser.parse_args()

    # Import SWE-bench and Docker
    try:
        from swebench.harness.utils import load_swebench_dataset
        import docker
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("\nInstall with:")
        print(
            "  pip install -e git+https://github.com/SWE-bench/SWE-bench"
        )
        print("  pip install docker")
        sys.exit(1)

    print(f"\n{'='*80}")
    print(f"🔬 SWE-bench In-Container Testing: {args.instance_id}")
    print(f"{'='*80}")

    # 1. Load instance
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

    # 2. Connect to Docker
    print("\n🐳 Connecting to Docker...")
    docker_client = docker.from_env()

    # Find SWE-bench image using pattern matching
    # SWE-bench creates images like: swebench/sweb.eval.x86_64.{repo}_{version}_{instance_id}:latest
    # e.g., swebench/sweb.eval.x86_64.astropy_1776_astropy-12907:latest

    print(
        f"   Searching for image matching instance {args.instance_id}..."
    )

    # Search for images that match the instance ID
    all_images = docker_client.images.list()
    matching_images = []

    if "__" in args.instance_id:
        issue_part = args.instance_id.split("__", 1)[1]
    else:
        issue_part = args.instance_id

    for img in all_images:
        for tag in img.tags:
            # Check if this tag matches: contains sweb.eval.x86_64 and ends with the issue part
            if "sweb.eval.x86_64" in tag and issue_part in tag:
                matching_images.append(tag)

    if not matching_images:
        print(
            f"❌ No Docker image found for instance {args.instance_id}"
        )
        print("\nYou need to build the image first:")
        print(f"  python -m swebench.harness.run_evaluation \\")
        print(f"    --dataset_name {args.dataset} \\")
        print(f"    --instance_ids {args.instance_id} \\")
        print(f"    --predictions_path gold \\")
        print(f"    --run_id test \\")
        print(f"    --cache_level instance")
        sys.exit(1)

    if len(matching_images) > 1:
        print(f"⚠️  Multiple images found, using first one:")
        for img in matching_images:
            print(f"   - {img}")

    image_name = matching_images[0]
    print(f"✓ Found image: {image_name}")

    # 3. Start container
    print("\n🚀 Starting container...")
    container = docker_client.containers.run(
        image=image_name,
        command="/bin/bash",
        detach=True,
        tty=True,
        stdin_open=True,
        working_dir="/testbed",
        auto_remove=False,
    )

    print(f"✓ Container started: {container.short_id}")

    try:
        # 4. Copy orchestrator code and requirements into container
        print("\n📦 Copying orchestrator code into container...")
        dt_package_path = str(Path(__file__).parent / "dt")
        copy_directory_to_container(
            container, dt_package_path, "/tmp/dt"
        )
        print("✓ Orchestrator code copied to /tmp/dt")

        # Install minimal dependencies (only what orchestrator needs)
        # righttyper is only needed on host, not in container
        # numpy should already be installed in SWE-bench containers
        print("\n📦 Installing dependencies in container...")
        minimal_deps = "hypothesis coverage libcst click pydantic rich jinja2 numpy"
        result = container.exec_run(
            ["pip", "install", "-q"] + minimal_deps.split(),
            stream=False,
        )
        if result.exit_code == 0:
            print("✓ Orchestrator dependencies installed")
        else:
            print(
                f"⚠️  Warning: Some dependencies may not have installed:"
            )
            print(result.output.decode())

        # Also ensure astropy dependencies are installed (erfa, etc.)
        print("📦 Installing project dependencies...")
        result = container.exec_run(
            ["pip", "install", "-q", "-e", "."],
            workdir="/testbed",
            stream=False,
        )
        if result.exit_code == 0:
            print("✓ Project dependencies installed")
        else:
            print(f"⚠️  Warning during project install:")
            if args.verbose:
                print(result.output.decode())

        # 5. Apply patch to create AFTER state (git will track BEFORE)
        print("\n🔧 Applying patch to /testbed...")

        # Write patch to container
        patch_escaped = patch.replace(
            "'", "'\"'\"'"
        )  # Escape single quotes for bash
        result = container.exec_run(
            [
                "/bin/bash",
                "-c",
                f"cat > /tmp/test.patch << 'PATCH_EOF'\n{patch}\nPATCH_EOF",
            ]
        )

        # Apply patch
        result = container.exec_run(
            ["git", "apply", "-v", "/tmp/test.patch"],
            workdir="/testbed",
        )

        if result.exit_code != 0:
            print(f"⚠️  git apply failed, trying patch command...")
            result = container.exec_run(
                ["patch", "-p1", "-i", "/tmp/test.patch"],
                workdir="/testbed",
            )

        if result.exit_code == 0:
            print("✓ Patch applied successfully")
        else:
            print(f"❌ Failed to apply patch: {result.output.decode()}")
            sys.exit(1)

        # 6. Parse patch to identify target file and function
        print("\n🎯 Identifying target file and function...")
        parser = PatchParser()
        python_files = parser.extract_python_files(patch)
        func_name = parser.get_primary_function(patch)

        if not python_files:
            print("❌ Could not identify Python file in patch")
            sys.exit(1)

        if not func_name:
            print("❌ Could not identify target function in patch")
            sys.exit(1)

        target_file = python_files[0]
        print(f"✓ Target file: {target_file}")
        print(f"✓ Target function: {func_name}")

        # 8. Extract test file if available
        test_file_in_container = None
        if instance.get("test_patch"):
            print("\n📝 Preparing test file for RightTyper...")
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False
            ) as f:
                local_test_file = f.name
                test_content = extract_test_file_from_patch(
                    instance["test_patch"], local_test_file
                )

            if test_content:
                test_file_in_container = "/tmp/test_context.py"
                copy_file_to_container(
                    container, local_test_file, test_file_in_container
                )
                os.unlink(local_test_file)
                print(f"✓ Test file ready: {test_file_in_container}")

        # 7. Create and copy test runner script
        print("\n📝 Creating test runner script...")
        test_script = create_test_runner_script(
            target_file=target_file,
            func_name=func_name,
            max_examples=args.max_examples,
            seed=args.seed,
            test_file_path=test_file_in_container,
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(test_script)
            local_script_path = f.name

        copy_file_to_container(
            container, local_script_path, "/tmp/run_test.py"
        )
        os.unlink(local_script_path)
        print("✓ Test runner copied to container")

        # 10. Run differential testing INSIDE container
        print(f"\n{'='*80}")
        print("🧪 Running Differential Testing Inside Container")
        print(f"{'='*80}\n")

        result = container.exec_run(
            ["python3", "/tmp/run_test.py"], stream=True, demux=True
        )

        # Stream output in real-time
        for stdout, stderr in result.output:
            if stdout:
                print(stdout.decode(), end="")
            if stderr:
                print(stderr.decode(), end="", file=sys.stderr)

        # 11. Extract report from container
        print("\n\n📊 Extracting report...")
        report_path = f"reports/{args.instance_id}.html"
        os.makedirs("reports", exist_ok=True)

        try:
            extract_file_from_container(
                container, "/tmp/report.html", report_path
            )
            print(f"✓ Report saved: {report_path}")
        except Exception as e:
            print(f"⚠️  Could not extract report: {e}")
            print(
                "   (This might be OK if testing failed before report generation)"
            )

        # Success!
        print(f"\n{'='*80}")
        print("✅ Testing Complete!")
        print(f"{'='*80}")
        print(f"📊 Report: {report_path}")

        if args.keep_container:
            print(
                f"\n🐳 Container kept for debugging: {container.short_id}"
            )
            print(
                f"   Connect with: docker exec -it {container.short_id} /bin/bash"
            )
            print(f"   Stop with: docker stop {container.short_id}")
            print(f"   Remove with: docker rm {container.short_id}")

    finally:
        if not args.keep_container:
            print("\n🧹 Cleaning up...")
            container.stop(timeout=10)
            container.remove()
            print("✓ Container removed")

    sys.exit(0)


if __name__ == "__main__":
    main()
