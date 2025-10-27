import inspect
from typing import Any, Callable, Dict, Optional, get_type_hints
from ..logger import get_logger


class TypeDiscoverer:
    """
    Responsible for discovering type information for function parameters.

    Discovery strategies (in priority order):
    1. Explicit type annotations (resolved from string annotations)
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

        Uses typing.get_type_hints() to properly resolve string annotations
        (from `from __future__ import annotations`) to actual type objects.

        This method only discovers types from the current
        function state (which may have been updated by RightTyper).

        Args:
            func: The function to analyze
            param_hints: Optional manually provided type hints

        Returns:
            Dictionary mapping parameter names to their types
        """
        # Get resolved type hints (handles string annotations)
        try:
            # Try to get type hints with module globals for better resolution
            module = inspect.getmodule(func)
            if module:
                # Include module globals and include_extras for generic types
                type_hints = get_type_hints(
                    func, globalns=module.__dict__, include_extras=True
                )
            else:
                type_hints = get_type_hints(func, include_extras=True)
        except NameError as e:
            # NameError often means TYPE_CHECKING imports are not available at runtime
            self.log.verbose(
                f"[TypeDiscoverer] Type hint resolution failed (TYPE_CHECKING import?): {e}"
            )
            # Fallback: resolve string annotations manually
            type_hints = {}
            module = inspect.getmodule(func)
            if hasattr(func, "__annotations__"):
                for (
                    param_name,
                    annotation,
                ) in func.__annotations__.items():
                    if param_name != "return":
                        # Try to resolve string annotation to actual type
                        resolved = self._resolve_string_annotation(
                            annotation, module
                        )
                        type_hints[param_name] = resolved
        except Exception as e:
            self.log.debug(
                f"[TypeDiscoverer] Could not resolve type hints: {e}"
            )
            # Last resort fallback: try raw annotations but resolve strings
            type_hints = {}
            module = inspect.getmodule(func)
            sig = inspect.signature(func)
            for param_name, param in sig.parameters.items():
                if param.annotation is not inspect.Parameter.empty:
                    # Try to resolve if it's a string
                    resolved = self._resolve_string_annotation(
                        param.annotation, module
                    )
                    type_hints[param_name] = resolved

        # Discover types for each parameter
        sig = inspect.signature(func)
        param_types = {}

        for param in sig.parameters.values():
            param_type = self._discover_param_type(
                param, type_hints, param_hints or {}
            )
            param_types[param.name] = param_type

        self.log.verbose(
            f"[TypeDiscoverer] Type discovered as {param_types}"
        )
        return param_types

    def _discover_param_type(
        self,
        param: inspect.Parameter,
        type_hints: Dict[str, Any],
        manual_hints: Dict[str, Any],
    ) -> Any:
        """
        Discover the type of a single parameter using multiple strategies.

        Priority:
        1. Resolved type annotation (from get_type_hints)
        2. Manual hints (provided by user)
        3. Default value type
        4. Fallback to Any

        Args:
            param: The parameter to discover type for
            type_hints: Resolved type hints from get_type_hints()
            manual_hints: User-provided manual hints

        Returns:
            The discovered type
        """
        # 1) Resolved type annotation (handles string annotations)
        if param.name in type_hints:
            self.log.verbose(
                f"[TypeDiscoverer] Found annotation for '{param.name}': {type_hints[param.name]}"
            )
            return type_hints[param.name]

        # 2) Manual hints
        if param.name in manual_hints:
            self.log.verbose(
                f"[TypeDiscoverer] Using manual hint for '{param.name}'"
            )
            return manual_hints[param.name]

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

    def _resolve_string_annotation(
        self, annotation: Any, module: Any
    ) -> Any:
        """
        Resolve a string annotation to an actual type object.

        For complex generics that can't be resolved (e.g., "np.ndarray[Any, DType]"),
        extracts the base type ("np.ndarray") and resolves it using module globals.

        Args:
            annotation: The annotation (could be string or already a type)
            module: The module to use for resolving names

        Returns:
            Resolved type object, or Any if resolution fails
        """
        import re

        # If it's not a string, return as-is
        if not isinstance(annotation, str):
            return annotation

        # Try basic type names
        basic_types = {
            "int": int,
            "str": str,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
        }

        if annotation in basic_types:
            return basic_types[annotation]

        # Extract base type from generic annotations
        # E.g., "np.ndarray[Any, numpy.dtypes.Float64DType]" -> "np.ndarray"
        base_type_match = re.match(r"^([a-zA-Z_][\w.]*)\[", annotation)
        if base_type_match:
            base_type_str = base_type_match.group(1)
            self.log.verbose(
                f"[TypeDiscoverer] Extracting base type '{base_type_str}' from '{annotation}'"
            )
            annotation = (
                base_type_str  # Continue resolving the base type
            )

        # Try to resolve using module globals (handles aliases like "np" -> numpy)
        if module and hasattr(module, "__dict__"):
            try:
                # Split by dots and resolve step by step
                parts = annotation.split(".")
                obj = module.__dict__.get(parts[0])

                if obj is not None:
                    # Traverse the rest of the path
                    for part in parts[1:]:
                        obj = getattr(obj, part)

                    self.log.verbose(
                        f"[TypeDiscoverer] Resolved '{annotation}' to {obj}"
                    )
                    return obj
            except Exception as e:
                self.log.debug(
                    f"[TypeDiscoverer] Could not resolve '{annotation}': {e}"
                )

        # Could not resolve - return Any
        self.log.verbose(
            f"[TypeDiscoverer] Could not resolve string annotation '{annotation}', using Any"
        )
        return Any
