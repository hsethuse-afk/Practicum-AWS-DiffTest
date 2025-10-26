"""
Git diff parser for automatic differential testing.

This module parses Git diffs to identify modified functions and extract
the before/after versions for differential testing.
"""

import ast
import re
import subprocess
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from .logger import get_logger


@dataclass
class ModifiedFunction:
    """Represents a modified function in a diff"""
    file_path: str
    function_name: str
    old_content: str  # Full file content before change
    new_content: str  # Full file content after change
    line_start: int  # Function start line in new version
    line_end: int    # Function end line in new version
    class_name: Optional[str] = None  # Class name if this is a method
    is_class_method: bool = False  # True if this is a class method


class GitDiffParser:
    """
    Parse Git diffs to identify modified functions.

    Supports:
    - Parsing git diff output
    - Identifying modified functions using AST
    - Extracting before/after file content
    """

    def __init__(self):
        self.log = get_logger()

    def parse_diff_from_commit(self, commit: str = "HEAD") -> List[ModifiedFunction]:
        """
        Parse a git commit diff to find modified functions.

        Args:
            commit: Git commit reference (e.g., "HEAD", "abc123", "HEAD~1")

        Returns:
            List of ModifiedFunction objects
        """
        # Get the diff
        diff_output = self._get_git_diff(commit)
        return self._parse_diff_output(diff_output, commit)

    def parse_diff_from_string(self, diff_string: str) -> List[ModifiedFunction]:
        """
        Parse a diff string (useful for testing or manual input).

        Args:
            diff_string: Raw git diff output

        Returns:
            List of ModifiedFunction objects
        """
        return self._parse_diff_output(diff_string, None)

    def parse_diff_from_file(self, diff_file_path: str, commit: Optional[str] = None) -> List[ModifiedFunction]:
        """
        Parse a diff file.

        Args:
            diff_file_path: Path to file containing git diff output
            commit: Optional commit reference for getting file content

        Returns:
            List of ModifiedFunction objects
        """
        with open(diff_file_path, 'r') as f:
            diff_string = f.read()
        return self._parse_diff_output(diff_string, commit)

    def _get_git_diff(self, commit: str) -> str:
        """Get git diff output for a commit"""
        try:
            # Get diff between commit and its parent
            cmd = ["git", "diff", f"{commit}^", commit]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            self.log.debug(f"[GitDiffParser] Git command failed: {e}")
            return ""

    def _parse_diff_output(
        self,
        diff_output: str,
        commit: Optional[str]
    ) -> List[ModifiedFunction]:
        """
        Parse git diff output to extract modified functions.

        Strategy:
        1. Parse diff to get changed files
        2. For each Python file, get old and new versions
        3. Use AST to find functions that were modified
        """
        modified_functions = []

        # Parse diff into file chunks
        file_diffs = self._split_diff_by_file(diff_output)

        for file_diff in file_diffs:
            if not file_diff['path'].endswith('.py'):
                continue

            # Get old and new file content
            old_content = self._get_old_file_content(
                file_diff['path'], commit
            )
            new_content = self._get_new_file_content(
                file_diff['path'], commit
            )

            if not old_content or not new_content:
                continue

            # Find modified functions
            changed_funcs = self._find_modified_functions(
                old_content,
                new_content,
                file_diff['changed_lines']
            )

            for func_name, line_start, line_end, class_name, is_class_method in changed_funcs:
                modified_functions.append(ModifiedFunction(
                    file_path=file_diff['path'],
                    function_name=func_name,
                    old_content=old_content,
                    new_content=new_content,
                    line_start=line_start,
                    line_end=line_end,
                    class_name=class_name,
                    is_class_method=is_class_method
                ))

        return modified_functions

    def _split_diff_by_file(self, diff_output: str) -> List[Dict]:
        """
        Split diff output into per-file chunks.

        Returns:
            List of dicts with 'path' and 'changed_lines'
        """
        file_diffs = []
        current_file = None
        changed_lines = []

        for line in diff_output.split('\n'):
            # New file marker
            if line.startswith('diff --git'):
                if current_file:
                    file_diffs.append({
                        'path': current_file,
                        'changed_lines': changed_lines
                    })
                # Extract file path - match the last b/ to get the new file path
                match = re.search(r' b/(.+)$', line)
                current_file = match.group(1) if match else None
                changed_lines = []

            # Track changed line numbers
            elif line.startswith('@@'):
                # Parse hunk header: @@ -old_start,old_count +new_start,new_count @@
                match = re.search(r'\+(\d+),?(\d+)?', line)
                if match:
                    start = int(match.group(1))
                    count = int(match.group(2)) if match.group(2) else 1
                    changed_lines.extend(range(start, start + count))

        # Add last file
        if current_file:
            file_diffs.append({
                'path': current_file,
                'changed_lines': changed_lines
            })

        return file_diffs

    def _get_old_file_content(
        self,
        file_path: str,
        commit: Optional[str]
    ) -> Optional[str]:
        """Get file content before the change"""
        if commit:
            try:
                cmd = ["git", "show", f"{commit}^:{file_path}"]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                return result.stdout
            except subprocess.CalledProcessError:
                return None
        return None

    def _get_new_file_content(
        self,
        file_path: str,
        commit: Optional[str]
    ) -> Optional[str]:
        """Get file content after the change"""
        if commit:
            try:
                cmd = ["git", "show", f"{commit}:{file_path}"]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                return result.stdout
            except subprocess.CalledProcessError:
                return None
        else:
            # If no commit, read from filesystem
            try:
                with open(file_path, 'r') as f:
                    return f.read()
            except Exception:
                return None

    def _find_modified_functions(
        self,
        old_content: str,
        new_content: str,
        changed_lines: List[int]
    ) -> List[Tuple[str, int, int, Optional[str], bool]]:
        """
        Use AST to find which functions were modified.

        Now identifies both module-level functions AND class methods.

        Args:
            old_content: File content before change
            new_content: File content after change
            changed_lines: Line numbers that changed

        Returns:
            List of (function_name, start_line, end_line, class_name, is_class_method) tuples
        """
        modified_functions = []

        try:
            # Parse new version to get function definitions
            new_tree = ast.parse(new_content)

            # Find MODULE-LEVEL functions
            for node in new_tree.body:
                if isinstance(node, ast.FunctionDef):
                    func_start = node.lineno
                    func_end = node.end_lineno or func_start

                    # Check if any changed line is within this function
                    if any(func_start <= line <= func_end for line in changed_lines):
                        modified_functions.append((
                            node.name,
                            func_start,
                            func_end,
                            None,  # No class name
                            False  # Not a class method
                        ))
                        self.log.debug(
                            f"[GitDiffParser] Found modified module-level function: {node.name}"
                        )

            # Find CLASS METHODS
            for node in new_tree.body:
                if isinstance(node, ast.ClassDef):
                    class_name = node.name

                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            func_start = item.lineno
                            func_end = item.end_lineno or func_start

                            # Check if any changed line is within this method
                            if any(func_start <= line <= func_end for line in changed_lines):
                                modified_functions.append((
                                    item.name,
                                    func_start,
                                    func_end,
                                    class_name,  # Class name
                                    True  # Is a class method
                                ))
                                self.log.verbose(
                                    f"[GitDiffParser] Found modified class method: {class_name}.{item.name} (lines {func_start}-{func_end})"
                                )

        except SyntaxError as e:
            self.log.debug(f"[GitDiffParser] Failed to parse Python file: {e}")

        return modified_functions
