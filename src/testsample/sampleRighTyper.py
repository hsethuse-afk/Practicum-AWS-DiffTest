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
        self,
        filepath: str,
        all_files=False,
        target_function=None,
        target_file=None,
        capture_output: bool = True,
    ) -> Dict[str, Any]:
        """
        Run righttyper on the specified Python file.

        Args:
            filepath: Path to the Python file to analyze
            capture_output: Whether to capture and return the output

        Returns:
            Dictionary containing stdout, stderr, return_code, output_files, and righttyper_output
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

        if all_files:
            cmd.append("--all-files")
        if target_file:
            cmd.append(f"--include-files {target_file}")
        if target_function:
            cmd.append(f"--include-files {target_function}")

        print(f"Running: {' '.join(cmd)}")

        result = {
            "command": cmd,
            "filepath": filepath,
            "output_dir": self.output_dir,
            "stdout": "",
            "stderr": "",
            "return_code": 0,
            "output_files": [],
            "righttyper_output": None,
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

            # Read and process righttyper.out file
            righttyper_out_path = "righttyper.out"
            if os.path.exists(righttyper_out_path):
                print(f"📖 Reading {righttyper_out_path}...")
                result["righttyper_output"] = self._process_righttyper_output(
                    righttyper_out_path
                )

                # Delete the file after processing
                print(f"🗑️  Deleting {righttyper_out_path}...")
                os.remove(righttyper_out_path)
            else:
                print(f"⚠️  {righttyper_out_path} not found")

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

    def _process_righttyper_output(self, filepath: str) -> Dict[str, Any]:
        """
        Read and process the righttyper.out file.

        Args:
            filepath: Path to the righttyper.out file

        Returns:
            Processed data from the file
        """
        try:
            with open(filepath, "r") as f:
                content = f.read()

            # Try to parse as JSON first
            try:
                data = json.loads(content)
                return {
                    "format": "json",
                    "data": data,
                    "raw_content": content
                }
            except json.JSONDecodeError:
                # If not JSON, return as plain text with some basic processing
                lines = content.strip().split("\n")
                return {
                    "format": "text",
                    "line_count": len(lines),
                    "lines": lines,
                    "raw_content": content
                }
        except Exception as e:
            return {
                "format": "error",
                "error": str(e),
                "raw_content": None
            }

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

        # Display righttyper.out processing results
        if result.get("righttyper_output"):
            print(f"\n📄 RIGHTTYPER.OUT CONTENT:")
            print("-" * 40)
            rt_output = result["righttyper_output"]

            if rt_output["format"] == "json":
                print(f"  Format: JSON")
                print(f"  Data: {json.dumps(rt_output['data'], indent=2)}")
            elif rt_output["format"] == "text":
                print(f"  Format: Text")
                print(f"  Line count: {rt_output['line_count']}")
                print(f"  Content preview:")
                for i, line in enumerate(rt_output['lines'][:10], 1):
                    print(f"    {i}: {line}")
                if rt_output['line_count'] > 10:
                    print(f"    ... ({rt_output['line_count'] - 10} more lines)")
            elif rt_output["format"] == "error":
                print(f"  ❌ Error reading file: {rt_output['error']}")

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

    def extract_function_type_hints(
        self, righttyper_content: str, function_name: str
    ) -> Dict[str, Any]:
        """
        Extract type hints for a specific function from righttyper output.

        Args:
            righttyper_content: Raw content from righttyper.out
            function_name: Name of the function to extract type hints for

        Returns:
            Dictionary containing parameter types and return type
        """
        lines = righttyper_content.strip().split("\n")
        result = {
            "function_name": function_name,
            "found": False,
            "original_signature": None,
            "typed_signature": None,
            "parameters": {},
            "return_type": None,
        }

        # Find the function in the output
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Check if this line is the function name
            if line == function_name:
                result["found"] = True

                # Look for the signatures (next non-empty lines after function name)
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1

                if j < len(lines):
                    result["original_signature"] = lines[j].strip()

                j += 1
                if j < len(lines):
                    typed_line = lines[j].strip()
                    result["typed_signature"] = typed_line

                    # Parse the typed signature to extract parameter types
                    if typed_line.startswith("+"):
                        typed_line = typed_line[1:].strip()  # Remove the '+'

                        # Extract function signature
                        import re
                        # Match pattern: def function_name(params) -> return_type:
                        match = re.match(
                            r"def\s+\w+\s*\((.*?)\)\s*(?:->\s*(.+?))?:",
                            typed_line,
                        )

                        if match:
                            params_str = match.group(1)
                            return_type = match.group(2)

                            if return_type:
                                result["return_type"] = return_type.strip()

                            # Parse parameters
                            if params_str:
                                params = [
                                    p.strip() for p in params_str.split(",")
                                ]
                                for param in params:
                                    if ":" in param:
                                        param_name, param_type = param.split(
                                            ":", 1
                                        )
                                        result["parameters"][
                                            param_name.strip()
                                        ] = param_type.strip()
                                    else:
                                        result["parameters"][param.strip()] = (
                                            "Any"
                                        )

                break
            i += 1

        return result


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

        # Example: Extract type hints for a specific function
        if result.get("righttyper_output") and result["righttyper_output"].get("raw_content"):
            print(f"\n{'='*60}")
            print("EXTRACTING TYPE HINTS FOR SPECIFIC FUNCTIONS")
            print(f"{'='*60}")

            # Extract type hints for 'is_happy' function
            function_name = "is_happy"
            type_hints = runner.extract_function_type_hints(
                result["righttyper_output"]["raw_content"],
                function_name
            )

            print(f"\n🔍 Function: {function_name}")
            if type_hints["found"]:
                print(f"  Found: ✅")
                print(f"  Original: {type_hints['original_signature']}")
                print(f"  Typed:    {type_hints['typed_signature']}")
                print(f"  Parameters:")
                for param, param_type in type_hints["parameters"].items():
                    print(f"    - {param}: {param_type}")
                print(f"  Return type: {type_hints['return_type']}")
            else:
                print(f"  Found: ❌ Function not found in output")

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
