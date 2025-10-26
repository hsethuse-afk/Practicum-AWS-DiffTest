import inspect
from typing import Any, Callable, Dict, Optional
from ..logger import get_logger


class TypeDiscoverer:
    """
    Responsible for discovering type information for function parameters.

    Discovery strategies (in priority order):
    1. Explicit type annotations
    2. Manual hints (provided by user)
    3. Default value types
    4. Fallback to typing.Any

    Note: Type inference (adding missing annotations) is handled separately
    by TypeInferenceEngine implementations in the Orchestrator.
    """

    def __init__(self):
        self.log = get_logger()

    def discover_param_types(
        self,
        func: Callable,
        param_hints: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Discover type information for all parameters of a function.

        Strategy:
        Discover types using priority: annotations → hints → defaults → Any

        Note: RightTyper execution and function reloading is handled by the
        Orchestrator, so this method only discovers types from the current
        function state (which may have been updated by RightTyper).

        Args:
            func: The function to analyze
            param_hints: Optional manually provided type hints

        Returns:
            Dictionary mapping parameter names to their types
        """
        # Discover types for each parameter
        sig = inspect.signature(func)
        param_types = {}

        for param in sig.parameters.values():
            param_type = self._discover_param_type(
                param, param_hints or {}
            )
            param_types[param.name] = param_type

        self.log.verbose(
            f"[TypeDiscoverer] Type discovered as {param_types}"
        )
        return param_types

    def _discover_param_type(
        self,
        param: inspect.Parameter,
        hints: Dict[str, Any],
    ) -> Any:
        """
        Discover the type of a single parameter using multiple strategies.

        Priority:
        1. Explicit annotation (may have been added by RightTyper)
        2. Manual hints
        3. Default value type
        4. Fallback to Any

        Note: RightTyper adds annotations directly to the function, so they
        will be picked up in step 1 after function reload.
        """
        # 1) Annotation (includes RightTyper-added annotations)
        if param.annotation is not inspect.Parameter.empty:
            self.log.verbose(
                f"[TypeDiscoverer] Found annotation for '{param.name}': {param.annotation}"
            )
            return param.annotation

        # 2) Manual hints
        if param.name in hints:
            self.log.verbose(
                f"[TypeDiscoverer] Using manual hint for '{param.name}'"
            )
            return hints[param.name]

        # 3) Default value type inference
        if param.default is not inspect.Parameter.empty:
            self.log.verbose(
                f"[TypeDiscoverer] Using default value type for '{param.name}'"
            )
            return type(param.default)

        # 4) Fallback
        self.log.verbose(
            f"[TypeDiscoverer] No type found for '{param.name}'"
        )
        return Any
