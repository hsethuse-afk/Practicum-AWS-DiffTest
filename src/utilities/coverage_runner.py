import os
import sys
import subprocess

def handle_coverage(source_dir: str = None):
    """
    If --coverage is in sys.argv, re-runs the current script with slipcover
    to generate a .coverage file.
    """
    if "--coverage" not in sys.argv:
        return

    if "SLIPCOVER_RUNNING" in os.environ:
        # In child process, continue with test run
        return
    else:
        # Parent process

        # 1. Run slipcover to generate JSON report
        print("Running tests with slipcover to generate slipcover.json...")
        slipcover_cmd = [
            sys.executable, "-m", "slipcover",
            "--json", "--out", "slipcover.json",
        ]
        if source_dir:
            slipcover_cmd.extend(["--source", source_dir])
        
        slipcover_cmd.extend(sys.argv)

        env = os.environ.copy()
        env["SLIPCOVER_RUNNING"] = "1"
        
        result = subprocess.run(slipcover_cmd, env=env)

        # 2. Create .coverage file from slipcover.json
        runner_dir = os.path.dirname(os.path.abspath(__file__))
        create_db_script_path = os.path.join(runner_dir, "create_coverage_db.py")
        if os.path.exists(create_db_script_path):
            print("\nConverting slipcover.json to .coverage format...")
            create_db_cmd = [sys.executable, create_db_script_path]
            subprocess.run(create_db_cmd)
        else:
            print(f"\nWarning: {create_db_script_path} not found. Skipping .coverage file creation.")

        # 3. Exit the parent process
        sys.exit(result.returncode)
