"""
Instance strategy planning for class method testing.

This module provides smart distribution of instances across test examples
to balance coverage of different instances with adequate testing per instance.
"""

import math
from typing import Tuple, Dict, Any, Optional
from ..logger import get_logger


class InstanceStrategyPlanner:
    """
    Plans how to distribute instance creation across test examples.

    For class methods, we need to balance:
    1. Testing with multiple different instances (diversity)
    2. Testing each instance multiple times (depth)

    This class calculates the optimal split given max_examples.
    """

    # Default instance distribution strategy
    # These can be customized based on testing needs
    MIN_INSTANCES = 1  # At least test with one instance
    MAX_INSTANCES = 20  # Cap instance diversity (avoid too sparse testing)
    MIN_EXAMPLES_PER_INSTANCE = 5  # Minimum tests per instance for meaningful results

    def __init__(self):
        self.log = get_logger()

    def calculate_distribution(
        self,
        max_examples: int,
        min_per_instance: int = None,
        max_instances: int = None,
        constructor_types: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, int]:
        """
        Calculate optimal instance distribution for testing.

        Strategy:
        - If constructor has no parameters or only simple types → use 1 instance
        - Otherwise, use square root heuristic for balanced diversity/depth
        - Ensure each instance gets minimum test examples
        - Cap maximum instances to avoid over-diversification

        Args:
            max_examples: Total number of test examples to run
            min_per_instance: Minimum examples per instance (default: MIN_EXAMPLES_PER_INSTANCE)
            max_instances: Maximum number of instances (default: MAX_INSTANCES)
            constructor_types: Constructor parameter types (if available)

        Returns:
            Tuple of (num_instances, examples_per_instance)
        """
        min_per = min_per_instance or self.MIN_EXAMPLES_PER_INSTANCE
        max_inst = max_instances or self.MAX_INSTANCES

        # Check if we should use just 1 instance
        if self._should_use_single_instance(constructor_types):
            self.log.verbose(
                f"[InstanceStrategyPlanner] Constructor has no/trivial parameters, using single instance"
            )
            return 1, max_examples

        # Calculate ideal number of instances
        # Use square root as heuristic: scales sublinearly with max_examples
        # This gives good balance between diversity and depth
        ideal_instances = max(self.MIN_INSTANCES, int(math.sqrt(max_examples)))

        # Cap at maximum instances
        ideal_instances = min(ideal_instances, max_inst)

        # Ensure we can meet minimum examples per instance
        max_possible_instances = max_examples // min_per
        num_instances = min(ideal_instances, max_possible_instances)

        # Ensure at least one instance
        num_instances = max(self.MIN_INSTANCES, num_instances)

        # Calculate examples per instance
        examples_per_instance = max_examples // num_instances

        self.log.verbose(
            f"[InstanceStrategyPlanner] Distribution: {num_instances} instances, "
            f"{examples_per_instance} examples each (total: {num_instances * examples_per_instance}/{max_examples})"
        )

        return num_instances, examples_per_instance

    def _should_use_single_instance(self, constructor_types: Optional[Dict[str, Any]]) -> bool:
        """
        Determine if we should use only a single instance for testing.

        Returns True if:
        - Constructor has no parameters (empty or None)
        - Constructor only has simple/primitive parameters with no diversity

        Args:
            constructor_types: Constructor parameter types

        Returns:
            True if single instance is sufficient, False otherwise
        """
        # No constructor parameters → all instances identical
        if not constructor_types or len(constructor_types) == 0:
            return True

        # Check if all parameters are simple types
        # For simple types with limited diversity, 1 instance may be enough
        # But for now, we'll be conservative and only return True for no params
        # Users can customize via the strategy JSON if needed

        return False

    def get_strategy_info(self, num_instances: int, examples_per_instance: int) -> str:
        """
        Generate human-readable info about the instance strategy.

        Args:
            num_instances: Number of unique instances
            examples_per_instance: Examples to test per instance

        Returns:
            Human-readable description
        """
        total = num_instances * examples_per_instance
        return (
            f"Testing with {num_instances} unique instance(s), "
            f"{examples_per_instance} test(s) per instance "
            f"(total: {total} tests)"
        )
