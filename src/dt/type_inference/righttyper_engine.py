"""
RightTyper implementation of TypeInferenceEngine.

RightTyper is a dynamic type inference tool that analyzes test execution traces
to infer types and add annotations to source code.
"""

import inspect
import os
import subprocess
import sys
from typing import Callable, Optional
from .type_inference_engine import TypeInferenceEngine


class RightTyperEngine(TypeInferenceEngine):
    """
    Type inference engine using RightTyper.

    RightTyper analyzes test executions to infer types and automatically
    adds type annotations to source files.

    Requirements:
    - Python 3.11+ (RightTyper uses typing.Self, typing.Never)
    - RightTyper installed: pip install git+https://github.com/GrammaTech/righttyper.git
    """

    def __init__(self):
        """
        Initialize RightTyper engine.

        By default, RightTyper will:
        - Use --all-files flag to analyze all imported modules
        - Use --include-files to include only .py files in the project directory
          (excludes Python standard library and site-packages)
        """
        super().__init__()  # Initialize logger from base class

    def needs_inference(
        self, func: Callable, test_file: Optional[str] = None
    ) -> bool:
        """
        Check if a function needs RightTyper inference.

        Preconditions:
        1. Test file must be provided and exist
        2. Function has at least one parameter without annotation

        Args:
            func: The function to check
            test_file: Path to test file (required for RightTyper)

        Returns:
            True if RightTyper should be run, False otherwise
        """
        # Precondition 1: Test file must be provided and exist
        if not test_file or not os.path.exists(test_file):
            self.log.debug(
                f"[{self.get_engine_name()}] No valid test file provided"
            )
            return False

        # Precondition 2: Check if any parameter is missing annotation
        sig = inspect.signature(func)
        missing_annotations = any(
            param.annotation is inspect.Parameter.empty
            for param in sig.parameters.values()
        )

        if not missing_annotations:
            self.log.debug(
                f"[{self.get_engine_name()}] All parameters already annotated"
            )
            return False

        self.log.verbose(
            f"[{self.get_engine_name()}] Function '{func.__name__}' needs type inference"
        )
        return True

    def run_inference(self, test_file: str) -> bool:
        """
        Run RightTyper to add type annotations to source files.

        Args:
            test_file: Path to test file that exercises target functions

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get directory and filename for relative path execution
            test_dir = os.path.dirname(os.path.abspath(test_file))
            test_filename = os.path.basename(test_file)

            # Get parent directory name to create a pattern that matches only local files
            # This prevents matching Python's standard library files
            parent_dir = os.path.basename(os.path.dirname(test_dir))
            if parent_dir:
                # Pattern to match files in parent directory only (e.g., "^demo-testing-repo/.*\.py$")
                include_pattern = f".*/{parent_dir}/.*\\.py$"
            else:
                # Fallback: match relative paths starting with ./ or direct filenames
                include_pattern = r"^(\./|\.\./|[^/]+\.py$)"

            cmd = [
                sys.executable,
                "-m",
                "righttyper",
                "--all-files",  # Analyze all imported modules
                "--include-files",
                include_pattern,  # Include only local project .py files
                test_filename,
                "--overwrite",  # Modify source files
                "--output-files",  # Required with --overwrite
            ]

            self.log.debug(
                f"[{self.get_engine_name()}] Running: {' '.join(cmd)} in {test_dir}"
            )

            # Run with test directory as cwd so imports work
            process_result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                cwd=test_dir,
            )

            # Log output for debugging
            if process_result.stderr:
                self.log.debug(
                    f"[{self.get_engine_name()}] stderr: {process_result.stderr}"
                )
            if process_result.stdout:
                self.log.debug(
                    f"[{self.get_engine_name()}] stdout: {process_result.stdout}"
                )

            # Check if successful
            if process_result.returncode != 0:
                self.log.debug(
                    f"[{self.get_engine_name()}] Exited with code {process_result.returncode}"
                )
                return False

            self.log.verbose(
                f"[{self.get_engine_name()}] Successfully added type annotations"
            )
            return True

        except Exception as e:
            self.log.debug(
                f"[{self.get_engine_name()}] Execution failed: {e}"
            )
            return False

    def get_engine_name(self) -> str:
        """Get the name of this engine."""
        return "RightTyper"
