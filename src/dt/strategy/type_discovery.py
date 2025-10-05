import inspect
import os
import re
import subprocess
import sys
from typing import Any, Callable, Dict, Optional
from ..logger import get_logger


class TypeDiscoverer:
    """
    Responsible for discovering type information for function parameters.
    Uses multiple strategies:
    1. Explicit annotations
    2. Manual hints
    3. Default value types
    4. RightTyper inference (when test file is provided)

    Note: RightTyper is run once per function (not per parameter) for efficiency.
    """

    def __init__(self):
        self.log = get_logger()

    def discover_param_types(
        self,
        func: Callable,
        test_file: Optional[str] = None,
        param_hints: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Discover type information for all parameters of a function.

        Args:
            func: The function to analyze
            test_file: Optional path to test file for RightTyper inference
            param_hints: Optional manually provided type hints

        Returns:
            Dictionary mapping parameter names to their types
        """
        sig = inspect.signature(func)
        param_types = {}

        # Run RightTyper once if needed (instead of per-parameter)
        righttyper_types = None
        if test_file is not None and os.path.exists(test_file):
            # Check if we need RightTyper (any param missing annotation, hint, and default)
            needs_righttyper = any(
                param.annotation is inspect.Parameter.empty
                and param.name not in (param_hints or {})
                and param.default is inspect.Parameter.empty
                for param in sig.parameters.values()
            )

            if needs_righttyper:
                self.log.verbose(
                    f"[TypeDiscoverer] Running RightTyper once for function '{func.__name__}' using {test_file}"
                )
                righttyper_types = (
                    self._infer_all_types_from_righttyper(
                        func, test_file
                    )
                )

        for param in sig.parameters.values():
            param_type = self._discover_param_type(
                param, righttyper_types, param_hints or {}
            )
            param_types[param.name] = param_type

        return param_types

    def _discover_param_type(
        self,
        param: inspect.Parameter,
        righttyper_types: Optional[Dict[str, Any]],
        hints: Dict[str, Any],
    ) -> Any:
        """
        Discover the type of a single parameter using multiple strategies.

        Priority:
        1. Explicit annotation
        2. Manual hints
        3. Default value type
        4. RightTyper inference (if available)
        5. Fallback to Any
        """
        # 1) Annotation
        if param.annotation is not inspect.Parameter.empty:
            self.log.verbose(
                f"[TypeDiscoverer] Found annotation for '{param.name}': {param.annotation}"
            )
            return param.annotation

        # 2) Manual hints
        if param.name in hints:
            self.log.verbose(
                f"[TypeDiscoverer] Using manual hint for '{param.name}'"
            )
            return hints[param.name]

        # 3) Default value type inference
        if param.default is not inspect.Parameter.empty:
            self.log.verbose(
                f"[TypeDiscoverer] Using default value type for '{param.name}'"
            )
            return type(param.default)

        # 4) RightTyper inference (from cached results)
        if righttyper_types and param.name in righttyper_types:
            self.log.verbose(
                f"[TypeDiscoverer] Using RightTyper inference for '{param.name}': {righttyper_types[param.name]}"
            )
            return righttyper_types[param.name]

        # 5) Fallback
        self.log.verbose(
            f"[TypeDiscoverer] No type found for '{param.name}'"
        )
        return Any

    def _infer_all_types_from_righttyper(
        self, func: Callable, test_file: str
    ) -> Dict[str, Any]:
        """
        Use RightTyper to infer types for all parameters of a function.

        Args:
            func: The target function
            test_file: Path to the test file that exercises the target function

        Returns:
            Dictionary mapping parameter names to their inferred types
        """
        try:
            # Run RightTyper on the test file directly
            righttyper_output = self._run_righttyper(test_file)

            if righttyper_output:
                # Extract types for all parameters
                param_types = (
                    self._extract_all_param_types_from_righttyper(
                        righttyper_output, func.__name__
                    )
                )
                if param_types:
                    self.log.verbose(
                        f"[TypeDiscoverer] RightTyper inference results: {param_types}"
                    )
                return param_types

        except Exception as e:
            self.log.debug(
                f"[TypeDiscoverer] RightTyper inference failed: {e}"
            )

        return {}

    def _run_righttyper(self, filepath: str) -> Optional[str]:
        """
        Run RightTyper on a file and return the output.

        Args:
            filepath: Path to the Python file to analyze

        Returns:
            Content of righttyper.out, or None if failed
        """
        try:
            cmd = [
                sys.executable,
                "-m",
                "righttyper",
                filepath,
                "--json-output",
            ]

            self.log.debug(f"[TypeDiscoverer] Running: {' '.join(cmd)}")

            # Run righttyper
            process_result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )

            # Read righttyper.out file
            righttyper_out_path = "righttyper.out"
            if os.path.exists(righttyper_out_path):
                with open(righttyper_out_path, "r") as f:
                    content = f.read()

                # Delete the file after reading
                os.remove(righttyper_out_path)
                self.log.debug(
                    f"[TypeDiscoverer] RightTyper output captured and cleaned up"
                )
                return content
            else:
                self.log.debug(
                    f"[TypeDiscoverer] righttyper.out not found"
                )
                return None

        except Exception as e:
            self.log.debug(
                f"[TypeDiscoverer] RightTyper execution failed: {e}"
            )
            return None

    def _extract_all_param_types_from_righttyper(
        self, righttyper_content: str, function_name: str
    ) -> Dict[str, Any]:
        """
        Extract types for all parameters from RightTyper output.

        Args:
            righttyper_content: Raw content from righttyper.out
            function_name: Name of the function

        Returns:
            Dictionary mapping parameter names to their types
        """
        lines = righttyper_content.strip().split("\n")
        param_types = {}

        # Find the function in the output
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Check if this line is the function name
            if line == function_name:
                # Look for the typed signature (starts with '+')
                j = i + 1
                while j < len(lines):
                    typed_line = lines[j].strip()
                    if typed_line.startswith("+"):
                        # Parse the typed signature
                        typed_line = typed_line[
                            1:
                        ].strip()  # Remove '+'

                        # Extract function signature using regex
                        # Match pattern: def function_name(params) -> return_type:
                        match = re.match(
                            r"def\s+\w+\s*\((.*?)\)\s*(?:->\s*(.+?))?:",
                            typed_line,
                        )

                        if match:
                            params_str = match.group(1)

                            # Parse all parameters
                            if params_str:
                                params = [
                                    p.strip()
                                    for p in params_str.split(",")
                                ]
                                for param in params:
                                    if ":" in param:
                                        p_name, p_type = param.split(
                                            ":", 1
                                        )
                                        # Convert string type to actual type
                                        param_types[p_name.strip()] = (
                                            self._parse_type_string(
                                                p_type.strip()
                                            )
                                        )
                        break
                    j += 1
                break
            i += 1

        return param_types

    def _parse_type_string(self, type_str: str) -> Any:
        """
        Convert a type string from RightTyper to an actual Python type.

        Args:
            type_str: Type as a string (e.g., "str", "int", "List[str]")

        Returns:
            The corresponding Python type
        """
        # Handle common basic types
        basic_types = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
        }

        if type_str in basic_types:
            return basic_types[type_str]

        # For complex types, return the string representation
        # The StrategySynthesizer will need to handle these
        return type_str
