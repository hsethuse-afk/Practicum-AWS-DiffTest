"""
Temporary file builder for differential testing.

Creates temporary files containing old and new versions of modified code,
preserving dependencies and imports.
"""

import os
import tempfile
from typing import Optional
from dataclasses import dataclass
from .git_diff_parser import ModifiedFunction
from .logger import get_logger


@dataclass
class TempFilePair:
    """Pair of temporary files for differential testing"""
    old_file: str  # Path to temporary file with old version
    new_file: str  # Path to temporary file with new version
    cleanup: callable  # Function to clean up temp files


class TempFileBuilder:
    """
    Build temporary files for differential testing.

    Creates isolated copies of files with old/new versions,
    preserving all dependencies and imports.
    """

    def __init__(self):
        self.log = get_logger()

    def build_temp_files(
        self,
        modified_func: ModifiedFunction,
        project_root: Optional[str] = None
    ) -> TempFilePair:
        """
        Create temporary files for old and new versions.

        Strategy:
        - If project_root is provided: Create temp files within the package structure
          to preserve relative imports
        - Otherwise: Create isolated temp files in /tmp

        Args:
            modified_func: ModifiedFunction object
            project_root: Optional project root directory to preserve package structure

        Returns:
            TempFilePair with paths to temporary files
        """
        if project_root:
            # Create temp files within the project structure to preserve imports
            return self._build_in_project(modified_func, project_root)
        else:
            # Legacy mode: isolated temp files (may fail with relative imports)
            return self._build_isolated(modified_func)

    def _build_isolated(
        self,
        modified_func: ModifiedFunction
    ) -> TempFilePair:
        """
        Create isolated temporary files (legacy mode).

        WARNING: This mode doesn't support relative imports.
        Use build_in_project for files with relative imports.
        """
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="difftest_")

        # Get base filename
        base_name = os.path.basename(modified_func.file_path)
        name, ext = os.path.splitext(base_name)

        # Create temp file paths
        old_file = os.path.join(temp_dir, f"{name}_old{ext}")
        new_file = os.path.join(temp_dir, f"{name}_new{ext}")

        # Write old version
        with open(old_file, 'w') as f:
            f.write(modified_func.old_content)

        # Write new version
        with open(new_file, 'w') as f:
            f.write(modified_func.new_content)

        self.log.verbose(
            f"[TempFileBuilder] Created temp files:\n"
            f"  Old: {old_file}\n"
            f"  New: {new_file}"
        )

        # Cleanup function
        def cleanup():
            try:
                os.remove(old_file)
                os.remove(new_file)
                os.rmdir(temp_dir)
                self.log.debug(
                    f"[TempFileBuilder] Cleaned up temp files in {temp_dir}"
                )
            except Exception as e:
                self.log.debug(
                    f"[TempFileBuilder] Failed to cleanup: {e}"
                )

        return TempFilePair(
            old_file=old_file,
            new_file=new_file,
            cleanup=cleanup
        )

    def _build_in_project(
        self,
        modified_func: ModifiedFunction,
        project_root: str
    ) -> TempFilePair:
        """
        Create temporary files within the project structure.

        This preserves the package hierarchy and allows relative imports to work.

        Args:
            modified_func: ModifiedFunction object
            project_root: Project root directory

        Returns:
            TempFilePair with paths to temporary files
        """
        # Get the original file path relative to project root
        file_path = modified_func.file_path

        # Determine the directory containing the file
        file_dir = os.path.dirname(file_path) if os.path.dirname(file_path) else "."
        target_dir = os.path.join(project_root, file_dir)

        # Ensure directory exists
        os.makedirs(target_dir, exist_ok=True)

        # Get base filename
        base_name = os.path.basename(file_path)
        name, ext = os.path.splitext(base_name)

        # Create temp file paths in the same directory as original file
        old_file = os.path.join(target_dir, f"{name}_old{ext}")
        new_file = os.path.join(target_dir, f"{name}_new{ext}")

        # Write old version
        with open(old_file, 'w') as f:
            f.write(modified_func.old_content)

        # Write new version
        with open(new_file, 'w') as f:
            f.write(modified_func.new_content)

        self.log.verbose(
            f"[TempFileBuilder] Created temp files in project:\n"
            f"  Old: {old_file}\n"
            f"  New: {new_file}"
        )

        # Cleanup function
        def cleanup():
            try:
                if os.path.exists(old_file):
                    os.remove(old_file)
                if os.path.exists(new_file):
                    os.remove(new_file)
                self.log.debug(
                    f"[TempFileBuilder] Cleaned up temp files"
                )
            except Exception as e:
                self.log.debug(
                    f"[TempFileBuilder] Failed to cleanup: {e}"
                )

        return TempFilePair(
            old_file=old_file,
            new_file=new_file,
            cleanup=cleanup
        )

    def build_with_dependencies(
        self,
        modified_func: ModifiedFunction,
        project_root: Optional[str] = None
    ) -> TempFilePair:
        """
        Create temporary files with external dependencies copied.

        For more complex scenarios where the modified file imports
        other project files, we need to copy the entire context.

        Args:
            modified_func: ModifiedFunction object
            project_root: Root directory of the project

        Returns:
            TempFilePair with paths to temporary files

        Note:
            This now uses build_temp_files with project_root to preserve
            package structure and relative imports.
        """
        # Use build_temp_files with project_root to preserve imports
        return self.build_temp_files(modified_func, project_root=project_root)
