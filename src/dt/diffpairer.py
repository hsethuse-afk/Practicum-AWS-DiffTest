from .contracts import TargetPair
from .git_diff_parser import GitDiffParser, ModifiedFunction
from .temp_file_builder import TempFileBuilder
from typing import List, Optional, Tuple


class DiffPairer:
    """
    Pairs old and new versions of functions for differential testing.

    Supports two modes:
    1. Manual mode: Accept two file paths and a function name
    2. Git diff mode: Parse git diff to automatically find modified functions
    """

    def __init__(self):
        self.git_parser = GitDiffParser()
        self.temp_builder = TempFileBuilder()

    def pair(
        self, file_a: str, file_b: str, func_name: str
    ) -> TargetPair:
        """
        Manual pairing mode: accept two file paths and a function name.

        Args:
            file_a: Path to old version file
            file_b: Path to new version file
            func_name: Function name to test

        Returns:
            TargetPair object
        """
        return TargetPair(
            file_a=file_a, file_b=file_b, func_name=func_name
        )

    def pair_from_git_commit(
        self,
        commit: str = "HEAD",
        func_name: Optional[str] = None
    ) -> List[Tuple[TargetPair, callable]]:
        """
        Git diff mode: parse commit to find modified functions.

        Args:
            commit: Git commit reference (e.g., "HEAD", "abc123")
            func_name: Optional filter for specific function name

        Returns:
            List of (TargetPair, cleanup_function) tuples
            The cleanup function should be called after testing to remove temp files
        """
        # Parse git diff
        modified_funcs = self.git_parser.parse_diff_from_commit(commit)

        # Filter by function name if specified
        if func_name:
            modified_funcs = [
                f for f in modified_funcs
                if f.function_name == func_name
            ]

        # Create temp files and target pairs
        pairs = []
        for mod_func in modified_funcs:
            temp_files = self.temp_builder.build_temp_files(mod_func)
            target = TargetPair(
                file_a=temp_files.old_file,
                file_b=temp_files.new_file,
                func_name=mod_func.function_name
            )
            pairs.append((target, temp_files.cleanup))

        return pairs

    def pair_from_diff_file(
        self,
        diff_file_path: str,
        func_name: Optional[str] = None,
        commit: Optional[str] = None,
        project_root: Optional[str] = None
    ) -> List[Tuple[TargetPair, callable]]:
        """
        Git diff mode: parse diff file to find modified functions.

        Args:
            diff_file_path: Path to file containing git diff
            func_name: Optional filter for specific function name
            commit: Optional commit reference for getting file content
            project_root: Optional project root to preserve package structure

        Returns:
            List of (TargetPair, cleanup_function) tuples
        """
        modified_funcs = self.git_parser.parse_diff_from_file(diff_file_path, commit)

        # Filter by function name if specified
        if func_name:
            modified_funcs = [
                f for f in modified_funcs
                if f.function_name == func_name
            ]

        # Now supporting both module-level functions AND class methods
        pairs = []
        for mod_func in modified_funcs:
            temp_files = self.temp_builder.build_temp_files(
                mod_func,
                project_root=project_root
            )
            target = TargetPair(
                file_a=temp_files.old_file,
                file_b=temp_files.new_file,
                func_name=mod_func.function_name,
                class_name=mod_func.class_name,
                is_class_method=mod_func.is_class_method,
            )
            pairs.append((target, temp_files.cleanup))

        return pairs

    def pair_from_patch(
        self,
        patch_file_path: str,
        func_name: Optional[str] = None
    ) -> List[Tuple[TargetPair, callable]]:
        """
        Patch-only mode: parse patch file without git commit context.
        Reconstructs old and new file content directly from the patch.

        Args:
            patch_file_path: Path to file containing git diff/patch
            func_name: Optional filter for specific function name

        Returns:
            List of (TargetPair, cleanup_function) tuples
        """
        # Use the new patch-only parser
        modified_funcs = self.git_parser.parse_patch_only(patch_file_path)

        # Filter by function name if specified
        if func_name:
            modified_funcs = [
                f for f in modified_funcs
                if f.function_name == func_name
            ]

        # Build temp files and target pairs
        pairs = []
        for mod_func in modified_funcs:
            temp_files = self.temp_builder.build_temp_files(mod_func)
            target = TargetPair(
                file_a=temp_files.old_file,
                file_b=temp_files.new_file,
                func_name=mod_func.function_name,
                class_name=mod_func.class_name,
                is_class_method=mod_func.is_class_method,
            )
            pairs.append((target, temp_files.cleanup))

        return pairs

    def pair_from_commit_dirs(
        self,
        before_project_root: str,
        after_project_root: str,
        diff_file_path: str,
        func_name: Optional[str] = None,
    ) -> List[Tuple[TargetPair, callable]]:
        """
        Create pairs from two complete project directories (before and after).

        This is the preferred method for differential testing as it preserves
        the full project structure and all dependencies in both versions.

        Args:
            before_project_root: Root directory of the project BEFORE changes
            after_project_root: Root directory of the project AFTER changes
            diff_file_path: Path to diff file showing the changes
            func_name: Optional filter for specific function name

        Returns:
            List of (TargetPair, cleanup_function) tuples
        """
        import os

        # Parse diff to find modified functions
        modified_funcs = self.git_parser.parse_diff_from_file(diff_file_path)

        # Filter by function name if specified
        if func_name:
            modified_funcs = [
                f for f in modified_funcs
                if f.function_name == func_name
            ]

        # Create target pairs pointing to actual files in each project directory
        pairs = []
        for mod_func in modified_funcs:
            # Build paths to the actual files in before/after directories
            file_a = os.path.join(before_project_root, mod_func.file_path)
            file_b = os.path.join(after_project_root, mod_func.file_path)

            # Verify files exist
            if not os.path.exists(file_a):
                raise FileNotFoundError(
                    f"Before file not found: {file_a}"
                )
            if not os.path.exists(file_b):
                raise FileNotFoundError(
                    f"After file not found: {file_b}"
                )

            target = TargetPair(
                file_a=file_a,
                file_b=file_b,
                func_name=mod_func.function_name,
                class_name=mod_func.class_name,
                is_class_method=mod_func.is_class_method,
            )

            # No temp files to cleanup since we're using actual project files
            no_cleanup = lambda: None
            pairs.append((target, no_cleanup))

        return pairs
