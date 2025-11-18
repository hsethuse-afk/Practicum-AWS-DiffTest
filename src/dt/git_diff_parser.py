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

    def parse_patch_only(self, patch_file_path: str) -> List[ModifiedFunction]:
        """
        Parse a patch file without git commit context.
        Reconstructs old and new file content from the patch itself.

        Args:
            patch_file_path: Path to file containing git diff/patch

        Returns:
            List of ModifiedFunction objects
        """
        with open(patch_file_path, 'r') as f:
            patch_content = f.read()

        return self._parse_patch_output(patch_content)

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
        current_line_num = 0  # Track current line number in new file

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
                current_line_num = 0

            # Track changed line numbers
            elif line.startswith('@@'):
                # Parse hunk header: @@ -old_start,old_count +new_start,new_count @@
                match = re.search(r'\+(\d+),?(\d+)?', line)
                if match:
                    current_line_num = int(match.group(1))

            # Track actual changes (not context lines)
            elif current_line_num > 0:
                if line.startswith('+') and not line.startswith('+++'):
                    # Added line - this is a real change in the new file
                    changed_lines.append(current_line_num)
                    current_line_num += 1
                elif line.startswith('-') and not line.startswith('---'):
                    # Removed line - doesn't exist in new file, but marks this area as changed
                    # We track the current position as changed (where the deletion happened)
                    changed_lines.append(current_line_num)
                    # Don't increment line number (deleted line doesn't exist in new file)
                elif not line.startswith('\\'):  # Ignore "\ No newline at end of file"
                    # Context line - increment but don't mark as changed
                    current_line_num += 1

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
        # If no commit, try reading from current filesystem (fallback)
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except Exception:
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

        Now identifies:
        - Module-level functions
        - Class methods
        - Nested functions (functions defined inside other functions)

        Strategy: Find the MOST SPECIFIC (innermost/smallest) function that contains the changes.

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

            # Collect all functions (including nested ones) with their ranges
            all_functions = []

            def visit_function(node, parent_class=None, depth=0):
                """Recursively visit all function definitions"""
                func_start = node.lineno
                func_end = node.end_lineno or func_start

                # Check if any changed line is within this function
                if any(func_start <= line <= func_end for line in changed_lines):
                    is_class_method = parent_class is not None
                    func_range = func_end - func_start

                    all_functions.append({
                        'name': node.name,
                        'start': func_start,
                        'end': func_end,
                        'class_name': parent_class,
                        'is_class_method': is_class_method,
                        'range': func_range,
                        'depth': depth
                    })

                # Recursively check nested functions (direct children only)
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        visit_function(item, parent_class, depth + 1)

            # Visit module-level functions
            for node in new_tree.body:
                if isinstance(node, ast.FunctionDef):
                    visit_function(node, None, 0)

            # Visit class methods
            for node in new_tree.body:
                if isinstance(node, ast.ClassDef):
                    class_name = node.name
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            visit_function(item, class_name, 0)

            # Find the MOST SPECIFIC (smallest range) function for each changed line
            # This ensures we get nested functions rather than their parents
            functions_by_specificity = {}

            for func in all_functions:
                # For each changed line this function contains
                for line in changed_lines:
                    if func['start'] <= line <= func['end']:
                        # If we haven't seen this line, or this function is more specific (smaller)
                        if line not in functions_by_specificity or \
                           func['range'] < functions_by_specificity[line]['range']:
                            functions_by_specificity[line] = func

            # Collect unique functions (same function might be most specific for multiple lines)
            # BUT filter out nested functions (depth > 0 and not a class method)
            seen = set()
            for func in functions_by_specificity.values():
                # Skip nested functions (functions defined inside other functions)
                # We only want:
                # - Module-level functions (depth == 0, no class)
                # - Class methods (depth == 0, has class)
                if func['depth'] > 0:
                    self.log.verbose(
                        f"[GitDiffParser] Skipping nested function: {func['name']} (lines {func['start']}-{func['end']}) - not callable at module level"
                    )
                    continue

                key = (func['name'], func['start'], func['end'], func['class_name'])
                if key not in seen:
                    seen.add(key)
                    modified_functions.append((
                        func['name'],
                        func['start'],
                        func['end'],
                        func['class_name'],
                        func['is_class_method']
                    ))

                    if func['class_name']:
                        self.log.verbose(
                            f"[GitDiffParser] Found modified class method: {func['class_name']}.{func['name']} (lines {func['start']}-{func['end']})"
                        )
                    else:
                        self.log.verbose(
                            f"[GitDiffParser] Found modified function: {func['name']} (lines {func['start']}-{func['end']})"
                        )

        except SyntaxError as e:
            self.log.debug(f"[GitDiffParser] Failed to parse Python file: {e}")

        return modified_functions

    def _parse_patch_output(self, patch_content: str) -> List[ModifiedFunction]:
        """
        Parse patch content and reconstruct old/new file versions.

        This method extracts file content from the patch itself without requiring
        access to a git repository or commit history.

        Strategy:
        1. Try to reconstruct from patch hunks
        2. If reconstruction produces incomplete files, try to read from filesystem
           and apply the patch to get complete versions

        Args:
            patch_content: Raw patch/diff content

        Returns:
            List of ModifiedFunction objects
        """
        modified_functions = []

        # Split patch into per-file chunks
        file_patches = self._split_patch_by_file(patch_content)

        for file_patch in file_patches:
            if not file_patch['path'].endswith('.py'):
                continue

            # Try to reconstruct old and new file content from the patch
            old_content, new_content = self._reconstruct_from_patch(
                file_patch['hunks'], file_patch['path']
            )

            if not old_content or not new_content:
                self.log.verbose(
                    f"[GitDiffParser] Could not reconstruct content from patch for {file_patch['path']}"
                )
                continue

            # Find modified functions using the same logic
            changed_funcs = self._find_modified_functions(
                old_content,
                new_content,
                file_patch['changed_lines']
            )

            for func_name, line_start, line_end, class_name, is_class_method in changed_funcs:
                modified_functions.append(ModifiedFunction(
                    file_path=file_patch['path'],
                    function_name=func_name,
                    old_content=old_content,
                    new_content=new_content,
                    line_start=line_start,
                    line_end=line_end,
                    class_name=class_name,
                    is_class_method=is_class_method
                ))

        return modified_functions

    def _split_patch_by_file(self, patch_content: str) -> List[Dict]:
        """
        Split patch content into per-file chunks with hunks.

        Returns:
            List of dicts with 'path', 'hunks', and 'changed_lines'
        """
        file_patches = []
        current_file = None
        current_hunks = []
        changed_lines = []
        current_line_num = 0
        current_hunk = None

        for line in patch_content.split('\n'):
            # New file marker
            if line.startswith('diff --git'):
                if current_file and current_hunks:
                    file_patches.append({
                        'path': current_file,
                        'hunks': current_hunks,
                        'changed_lines': changed_lines
                    })
                # Extract file path
                match = re.search(r' b/(.+)$', line)
                current_file = match.group(1) if match else None
                current_hunks = []
                changed_lines = []
                current_line_num = 0
                current_hunk = None

            # Hunk header
            elif line.startswith('@@'):
                if current_hunk:
                    current_hunks.append(current_hunk)
                # Parse: @@ -old_start,old_count +new_start,new_count @@
                old_match = re.search(r'-(\d+),?(\d+)?', line)
                new_match = re.search(r'\+(\d+),?(\d+)?', line)

                if old_match and new_match:
                    old_start = int(old_match.group(1))
                    old_count = int(old_match.group(2)) if old_match.group(2) else 1
                    new_start = int(new_match.group(1))
                    new_count = int(new_match.group(2)) if new_match.group(2) else 1

                    current_hunk = {
                        'old_start': old_start,
                        'old_count': old_count,
                        'new_start': new_start,
                        'new_count': new_count,
                        'lines': []
                    }
                    current_line_num = new_start

            # Hunk content
            elif current_hunk is not None:
                if line.startswith('---') or line.startswith('+++'):
                    continue  # Skip file headers
                elif line.startswith('+') and not line.startswith('+++'):
                    current_hunk['lines'].append(('add', line[1:]))
                    changed_lines.append(current_line_num)
                    current_line_num += 1
                elif line.startswith('-') and not line.startswith('---'):
                    current_hunk['lines'].append(('remove', line[1:]))
                    changed_lines.append(current_line_num)
                elif not line.startswith('\\'):  # Ignore "\ No newline at end of file"
                    current_hunk['lines'].append(('context', line[1:] if line else ''))
                    current_line_num += 1

        # Add last hunk and file
        if current_hunk:
            current_hunks.append(current_hunk)
        if current_file and current_hunks:
            file_patches.append({
                'path': current_file,
                'hunks': current_hunks,
                'changed_lines': changed_lines
            })

        return file_patches

    def _reconstruct_from_patch(self, hunks: List[Dict], file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Reconstruct old and new file content from patch hunks.

        Strategy:
        1. If hunks cover the entire file (start at line 1), reconstruct from hunks
        2. Otherwise, try to read the file from filesystem and apply patches
        3. If filesystem read fails, still try hunk-only reconstruction

        Args:
            hunks: List of hunk dictionaries with old_start, new_start, and lines
            file_path: Path to the file being patched

        Returns:
            Tuple of (old_content, new_content) as strings, or (None, None) if reconstruction fails
        """
        if not hunks:
            return None, None

        try:
            # Check if this is a full file or just fragments
            # If the first hunk starts near the beginning (within first few lines),
            # it's likely a full file
            first_hunk_starts_early = hunks[0]['new_start'] <= 5

            # Try to read from filesystem first if available
            file_content = None
            try:
                with open(file_path, 'r') as f:
                    file_content = f.read()
                self.log.verbose(f"[GitDiffParser] Read current file from filesystem: {file_path}")
            except Exception:
                # File doesn't exist or can't be read - that's OK
                pass

            # If we have the file and hunks don't start at beginning, apply patches
            if file_content and not first_hunk_starts_early:
                return self._apply_patch_to_content(file_content, hunks)

            # Otherwise, reconstruct from hunks only
            old_lines = []
            new_lines = []

            # Process each hunk
            for hunk in hunks:
                # Add lines from this hunk
                for line_type, line_content in hunk['lines']:
                    if line_type == 'context':
                        # Context lines appear in both versions
                        old_lines.append(line_content)
                        new_lines.append(line_content)
                    elif line_type == 'remove':
                        # Removed lines only in old version
                        old_lines.append(line_content)
                    elif line_type == 'add':
                        # Added lines only in new version
                        new_lines.append(line_content)

            old_content = '\n'.join(old_lines)
            new_content = '\n'.join(new_lines)

            # If we have file content and the reconstruction looks incomplete, use file + patches
            if file_content:
                # Check if reconstructed content looks complete (has reasonable length)
                file_lines = len(file_content.split('\n'))
                reconstructed_lines = len(new_lines)

                # If reconstruction has significantly fewer lines than the file, use patch application
                if reconstructed_lines < file_lines * 0.5:
                    self.log.verbose(
                        f"[GitDiffParser] Patch appears incomplete ({reconstructed_lines} vs {file_lines} lines), applying to full file"
                    )
                    return self._apply_patch_to_content(file_content, hunks)

            return old_content, new_content

        except Exception as e:
            self.log.debug(f"[GitDiffParser] Failed to reconstruct from patch: {e}")
            return None, None

    def _apply_patch_to_content(self, file_content: str, hunks: List[Dict]) -> Tuple[str, str]:
        """
        Apply patch hunks to existing file content to get old and new versions.

        This reconstructs the old version by reversing the patch operations:
        - Remove lines that were added (marked with +)
        - Add back lines that were removed (marked with -)

        Args:
            file_content: Current file content (assumed to be the 'new' version)
            hunks: List of patch hunks

        Returns:
            Tuple of (old_content, new_content)
        """
        # The file content we read is the NEW version
        new_content = file_content
        new_lines = file_content.split('\n')
        old_lines = []

        # Build old content by going through hunks in order and reconstructing
        current_new_pos = 0  # Track position in new file

        for hunk in hunks:
            hunk_new_start = hunk['new_start'] - 1  # Convert to 0-based
            hunk_old_start = hunk['old_start'] - 1  # Convert to 0-based

            # Copy unchanged lines before this hunk
            while current_new_pos < hunk_new_start:
                if current_new_pos < len(new_lines):
                    old_lines.append(new_lines[current_new_pos])
                current_new_pos += 1

            # Process the hunk
            for line_type, line_content in hunk['lines']:
                if line_type == 'context':
                    # Context lines appear in both versions
                    old_lines.append(line_content)
                    current_new_pos += 1
                elif line_type == 'remove':
                    # Removed line only in old version
                    old_lines.append(line_content)
                    # Don't increment new_pos (line doesn't exist in new)
                elif line_type == 'add':
                    # Added line only in new version
                    # Don't add to old_lines (line doesn't exist in old)
                    current_new_pos += 1

        # Copy remaining lines after last hunk
        while current_new_pos < len(new_lines):
            old_lines.append(new_lines[current_new_pos])
            current_new_pos += 1

        old_content = '\n'.join(old_lines)
        return old_content, new_content
