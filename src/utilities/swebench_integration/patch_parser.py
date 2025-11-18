"""
Parse git patches to extract information about code changes.

This module provides utilities to analyze unified diff patches and extract
useful information like modified files, changed functions, and code additions.
"""

import re
import ast
from typing import List, Dict, Set, Tuple, Optional
from collections import Counter


class PatchParser:
    """Parser for unified diff patches (git diff format)."""

    @staticmethod
    def extract_modified_files(patch: str) -> List[str]:
        """
        Extract list of files modified in the patch.

        Args:
            patch: Unified diff patch content

        Returns:
            List of file paths that were modified

        Example:
            >>> patch = "diff --git a/src/foo.py b/src/foo.py\\n..."
            >>> PatchParser.extract_modified_files(patch)
            ['src/foo.py']
        """
        # Match "diff --git a/path/to/file.py b/path/to/file.py"
        pattern = r'^diff --git a/(.*?) b/'
        files = re.findall(pattern, patch, re.MULTILINE)
        return list(dict.fromkeys(files))  # Preserve order, remove duplicates

    @staticmethod
    def extract_changed_functions(patch: str) -> List[str]:
        """
        Identify function names that were modified in the patch.

        Args:
            patch: Unified diff patch content

        Returns:
            List of function names that appear in the patch context

        Example:
            >>> patch = "- def old_func():\\n+ def new_func():\\n"
            >>> PatchParser.extract_changed_functions(patch)
            ['old_func', 'new_func']
        """
        functions = []

        # First, try to extract from hunk headers like: @@ ... @@ def foo(...)
        hunk_pattern = r'@@[^@]+@@\s+def\s+([a-zA-Z_][a-zA-Z0-9_]*)\('
        hunk_functions = re.findall(hunk_pattern, patch)
        functions.extend(hunk_functions)

        # Also match function definitions in diff context (lines starting with +, -, or space)
        pattern = r'^[ +-]def ([a-zA-Z_][a-zA-Z0-9_]*)\('
        context_functions = re.findall(pattern, patch, re.MULTILINE)
        functions.extend(context_functions)

        # Return unique functions, preserving order
        return list(dict.fromkeys(functions))

    @staticmethod
    def get_primary_function(patch: str) -> Optional[str]:
        """
        Identify the primary function that was modified.

        Uses heuristics to determine which function is most likely the main target:
        1. Most frequently mentioned function
        2. Function with most changes

        Args:
            patch: Unified diff patch content

        Returns:
            Name of the primary function, or None if no functions found

        Example:
            >>> patch = "def foo():\\n  pass\\ndef foo():\\n  return 1"
            >>> PatchParser.get_primary_function(patch)
            'foo'
        """
        functions = PatchParser.extract_changed_functions(patch)

        if not functions:
            return None

        # Count frequency of each function
        counter = Counter(functions)

        # Return most common function
        return counter.most_common(1)[0][0]

    @staticmethod
    def extract_additions(patch: str) -> str:
        """
        Extract only the added lines from the patch.

        Args:
            patch: Unified diff patch content

        Returns:
            String containing only the added lines ('+' prefix removed)

        Example:
            >>> patch = "- old line\\n+ new line\\n  context"
            >>> PatchParser.extract_additions(patch)
            'new line'
        """
        lines = []
        for line in patch.split('\n'):
            # Added lines start with '+' but not '+++'
            if line.startswith('+') and not line.startswith('+++'):
                lines.append(line[1:])  # Remove '+' prefix

        return '\n'.join(lines)

    @staticmethod
    def extract_deletions(patch: str) -> str:
        """
        Extract only the deleted lines from the patch.

        Args:
            patch: Unified diff patch content

        Returns:
            String containing only the deleted lines ('-' prefix removed)

        Example:
            >>> patch = "- old line\\n+ new line\\n  context"
            >>> PatchParser.extract_deletions(patch)
            'old line'
        """
        lines = []
        for line in patch.split('\n'):
            # Deleted lines start with '-' but not '---'
            if line.startswith('-') and not line.startswith('---'):
                lines.append(line[1:])  # Remove '-' prefix

        return '\n'.join(lines)

    @staticmethod
    def get_change_summary(patch: str) -> Dict[str, int]:
        """
        Get summary statistics about the patch.

        Args:
            patch: Unified diff patch content

        Returns:
            Dictionary with change statistics:
            - files_changed: Number of files modified
            - lines_added: Number of lines added
            - lines_deleted: Number of lines deleted
            - functions_changed: Number of functions modified

        Example:
            >>> summary = PatchParser.get_change_summary(patch)
            >>> summary['lines_added']
            42
        """
        additions = PatchParser.extract_additions(patch)
        deletions = PatchParser.extract_deletions(patch)

        return {
            'files_changed': len(PatchParser.extract_modified_files(patch)),
            'lines_added': len([l for l in additions.split('\n') if l.strip()]),
            'lines_deleted': len([l for l in deletions.split('\n') if l.strip()]),
            'functions_changed': len(PatchParser.extract_changed_functions(patch)),
        }

    @staticmethod
    def extract_function_signature(patch: str, func_name: str) -> Optional[str]:
        """
        Extract the full signature of a specific function from the patch.

        Args:
            patch: Unified diff patch content
            func_name: Name of the function to find

        Returns:
            Full function signature (e.g., "def foo(x: int, y: str) -> bool:")
            or None if not found

        Example:
            >>> patch = "+ def calculate(x: int) -> int:"
            >>> PatchParser.extract_function_signature(patch, 'calculate')
            'def calculate(x: int) -> int:'
        """
        # Match function definition with the given name
        pattern = rf'^[ +-](def {re.escape(func_name)}\([^)]*\)(?:\s*->\s*[^:]+)?:)'
        matches = re.findall(pattern, patch, re.MULTILINE)

        if matches:
            return matches[0]

        return None

    @staticmethod
    def parse_hunk_headers(patch: str) -> List[Dict[str, int]]:
        """
        Parse hunk headers to understand where changes occurred.

        Hunk headers look like: @@ -10,5 +10,6 @@

        Args:
            patch: Unified diff patch content

        Returns:
            List of dictionaries with hunk information:
            - old_start: Starting line in old file
            - old_count: Number of lines in old file
            - new_start: Starting line in new file
            - new_count: Number of lines in new file

        Example:
            >>> hunks = PatchParser.parse_hunk_headers(patch)
            >>> hunks[0]['old_start']
            10
        """
        # Match @@ -old_start,old_count +new_start,new_count @@
        pattern = r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@'
        matches = re.findall(pattern, patch, re.MULTILINE)

        hunks = []
        for match in matches:
            old_start, old_count, new_start, new_count = match
            hunks.append({
                'old_start': int(old_start),
                'old_count': int(old_count) if old_count else 1,
                'new_start': int(new_start),
                'new_count': int(new_count) if new_count else 1,
            })

        return hunks

    @staticmethod
    def extract_file_patch(full_patch: str, file_path: str) -> str:
        """
        Extract the patch content for a specific file.

        Args:
            full_patch: Complete patch with multiple files
            file_path: Path to the file to extract

        Returns:
            Patch content for just that file

        Example:
            >>> file_patch = PatchParser.extract_file_patch(patch, 'src/foo.py')
        """
        lines = full_patch.split('\n')
        result = []
        capturing = False

        for i, line in enumerate(lines):
            # Start capturing when we find the file header
            if line.startswith('diff --git') and file_path in line:
                capturing = True

            # Stop capturing when we hit the next file
            elif line.startswith('diff --git') and capturing:
                break

            # Capture lines while in the target file
            if capturing:
                result.append(line)

        return '\n'.join(result)

    @staticmethod
    def is_python_file(file_path: str) -> bool:
        """
        Check if a file path is a Python file.

        Args:
            file_path: Path to check

        Returns:
            True if the file is a Python file (.py extension)

        Example:
            >>> PatchParser.is_python_file('src/foo.py')
            True
            >>> PatchParser.is_python_file('README.md')
            False
        """
        return file_path.endswith('.py')

    @staticmethod
    def extract_python_files(patch: str) -> List[str]:
        """
        Extract only Python files from the patch.

        Args:
            patch: Unified diff patch content

        Returns:
            List of Python file paths (.py files only)

        Example:
            >>> PatchParser.extract_python_files(patch)
            ['src/module.py', 'tests/test_module.py']
        """
        all_files = PatchParser.extract_modified_files(patch)
        return [f for f in all_files if PatchParser.is_python_file(f)]

    @staticmethod
    def extract_class_changes(patch: str) -> List[str]:
        """
        Extract class names that were modified in the patch.

        Args:
            patch: Unified diff patch content

        Returns:
            List of class names that appear in the patch

        Example:
            >>> PatchParser.extract_class_changes(patch)
            ['MyClass', 'AnotherClass']
        """
        # Match class definitions in diff context
        pattern = r'^[ +-]class ([a-zA-Z_][a-zA-Z0-9_]*)'
        classes = re.findall(pattern, patch, re.MULTILINE)

        # Return unique classes, preserving order
        return list(dict.fromkeys(classes))
