#!/usr/bin/env python3
"""
Simple script to run righttyper on a Python file and capture the output.
"""

import subprocess
import sys
import os
import json
from pathlib import Path
from typing import Dict, Any


class RighttyperRunner:
    def __init__(self, output_dir: str = "righttyper_output"):
        self.output_dir = output_dir

    def run_righttyper(
        self, filepath: str, capture_output: bool = True
    ) -> Dict[str, Any]:
        """
        Run righttyper on the specified Python file.

        Args:
            filepath: Path to the Python file to analyze
            capture_output: Whether to capture and return the output

        Returns:
            Dictionary containing stdout, stderr, return_code, and output_files
        """
        # Ensure the file exists
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)

        # Prepare the command
        cmd = [
            sys.executable,
            "-m",
            "righttyper",
            filepath,
            "--json-output",
        ]

        print(f"Running: {' '.join(cmd)}")

        result = {
            "command": cmd,
            "filepath": filepath,
            "output_dir": self.output_dir,
            "stdout": "",
            "stderr": "",
            "return_code": 0,
            "output_files": [],
            "success": False,
        }

        try:
            # Run righttyper
            process_result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                check=False,  # Don't raise exception on non-zero exit
            )

            result["stdout"] = process_result.stdout
            result["stderr"] = process_result.stderr
            result["return_code"] = process_result.returncode
            result["success"] = process_result.returncode == 0

            # Find output files
            if os.path.exists(self.output_dir):
                output_files = list(Path(self.output_dir).rglob("*"))
                result["output_files"] = [
                    str(f) for f in output_files if f.is_file()
                ]

        except Exception as e:
            result["stderr"] = str(e)
            result["success"] = False

        return result

    def print_results(self, result: Dict[str, Any]):
        """Print the results in a nice format."""
        print(f"\n{'='*60}")
        print(f"RIGHTTYPER ANALYSIS RESULTS")
        print(f"{'='*60}")
        print(f"File: {result['filepath']}")
        print(
            f"Status: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}"
        )
        print(f"Return Code: {result['return_code']}")
        print(f"Output Directory: {result['output_dir']}")

        if result["stdout"]:
            print(f"\n📤 STDOUT:")
            print("-" * 40)
            print(result["stdout"])

        if result["stderr"]:
            print(f"\n⚠️  STDERR:")
            print("-" * 40)
            print(result["stderr"])

        if result["output_files"]:
            print(f"\n📁 OUTPUT FILES:")
            print("-" * 40)
            for file in result["output_files"]:
                print(f"  • {file}")

                # If it's a JSON file, try to show a preview
                if file.endswith(".json"):
                    try:
                        with open(file, "r") as f:
                            data = json.load(f)
                        print(
                            f"    Preview: {json.dumps(data, indent=2)[:200]}..."
                        )
                    except:
                        pass
        else:
            print(f"\n📁 No output files generated")

    def save_results(
        self,
        result: Dict[str, Any],
        results_file: str = "righttyper_results.json",
    ):
        """Save the results to a JSON file."""
        results_path = os.path.join(self.output_dir, results_file)
        with open(results_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\n💾 Results saved to: {results_path}")
        return results_path


def main():

    filepath = "./testsample/test.py"

    # Create runner instance
    runner = RighttyperRunner()

    try:
        print(f"🚀 Running righttyper analysis on: {filepath}")

        # Run righttyper
        result = runner.run_righttyper(filepath)

        # Print results
        runner.print_results(result)

        # Save results
        runner.save_results(result)

        if result["success"]:
            print(f"\n🎉 Analysis completed successfully!")
        else:
            print(
                f"\n💥 Analysis failed with return code {result['return_code']}"
            )
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
