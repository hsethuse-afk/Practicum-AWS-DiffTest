"""
SWE-bench Integration Module

This module provides utilities for integrating the differential testing framework
with the SWE-bench benchmark dataset.

Components:
- PatchParser: Parse git patches to extract files, functions, and changes
- DockerManager: Manage SWE-bench Docker containers
- test_utils: Helper functions for extracting test files from patches

Note: Type inference is handled by the existing RightTyper engine in dt/type_inference/
"""

from .patch_parser import PatchParser
from .docker_manager import DockerManager

__all__ = ['PatchParser', 'DockerManager']
