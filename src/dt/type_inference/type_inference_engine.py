"""
Abstract base class for type inference engines.

Type inference engines add type annotations to source code by analyzing
test executions or static analysis. Different engines can be plugged in
as needed (RightTyper, MonkeyType, Pytype, etc.).
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional
from ..logger import get_logger


class TypeInferenceEngine(ABC):
    """
    Abstract base class for type inference engines.

    A type inference engine is responsible for:
    1. Determining if a function needs type inference
    2. Running the inference tool to add annotations to source files

    Implementations include: RightTyper, MonkeyType, Pytype, etc.
    """

    def __init__(self):
        self.log = get_logger()

    @abstractmethod
    def needs_inference(self, func: Callable, test_file: Optional[str] = None) -> bool:
        """
        Check if a function needs type inference.

        Args:
            func: The function to check
            test_file: Optional test file path (required by some engines)

        Returns:
            True if type inference should be run, False otherwise
        """
        pass

    @abstractmethod
    def run_inference(self, test_file: str) -> bool:
        """
        Run type inference to add annotations to source files.

        This method should:
        1. Execute the type inference tool (e.g., righttyper, monkeytype)
        2. Modify source files with inferred type annotations
        3. Return success/failure status

        Args:
            test_file: Path to test file that exercises the target functions

        Returns:
            True if inference succeeded, False otherwise
        """
        pass

    def get_engine_name(self) -> str:
        """
        Get the name of this inference engine.

        Returns:
            Human-readable name (e.g., "RightTyper", "MonkeyType")
        """
        return self.__class__.__name__
