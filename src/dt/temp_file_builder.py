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
        modified_func: ModifiedFunction
    ) -> TempFilePair:
        """
        Create temporary files for old and new versions.

        Strategy:
        - Create temp files with the full file content (including dependencies)
        - Old version: original file content
        - New version: modified file content

        Args:
            modified_func: ModifiedFunction object

        Returns:
            TempFilePair with paths to temporary files
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
            This is a future enhancement for handling complex dependencies.
            Currently just uses the simple build_temp_files approach.
        """
        # TODO: Implement dependency resolution and copying
        # For now, use simple approach
        return self.build_temp_files(modified_func)
