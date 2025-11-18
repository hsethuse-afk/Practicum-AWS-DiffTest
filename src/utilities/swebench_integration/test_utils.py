"""
Utilities for extracting test files from SWE-bench patches.

This module provides simple helpers to extract test code from test_patch fields,
which can then be passed to the existing RightTyper engine for type inference.
"""

import os
from typing import Optional
from .patch_parser import PatchParser


def extract_test_file_from_patch(
    test_patch: str,
    output_path: str
) -> Optional[str]:
    """
    Extract test code from a test_patch and save to a file.

    The test file can then be passed to the Orchestrator's run_pair() method
    as the test_file parameter, allowing RightTyper to infer types.

    Args:
        test_patch: Test patch content from SWE-bench instance
        output_path: Where to save the extracted test file

    Returns:
        Path to saved test file, or None if no test code found

    Example:
        >>> test_file = extract_test_file_from_patch(
        ...     instance['test_patch'],
        ...     'temp/test_context.py'
        ... )
        >>> # Pass to orchestrator
        >>> orch.run_pair(..., test_file=test_file)
    """
    if not test_patch or not test_patch.strip():
        return None

    # Extract added lines from patch (these are the new tests)
    test_code = PatchParser.extract_additions(test_patch)

    if not test_code.strip():
        return None

    # Ensure parent directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save test code to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(test_code)

    return output_path


def has_test_code(test_patch: str) -> bool:
    """
    Check if a test_patch contains actual test code.

    Args:
        test_patch: Test patch content

    Returns:
        True if patch contains test code, False otherwise

    Example:
        >>> if has_test_code(instance['test_patch']):
        ...     test_file = extract_test_file_from_patch(...)
    """
    if not test_patch:
        return False

    test_code = PatchParser.extract_additions(test_patch)
    return bool(test_code.strip())
