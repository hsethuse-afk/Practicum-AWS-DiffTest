import inspect
import re
from dataclasses import dataclass
from typing import (
    Any, Callable, Dict, List, Optional, Set, Tuple, Union,
    get_origin, get_args
)
from decimal import Decimal
from datetime import datetime, date, time
from hypothesis import strategies as st

from .contracts import StrategyPlan
from .logger import get_logger


@dataclass
class TypeAnalysis:
    """Analysis result for a function parameter."""
    param_name: str
    primary_type: type
    nullable: bool = False
    constraints: Dict[str, Any] = None
    suggested_strategy: Optional[st.SearchStrategy] = None
    confidence: float = 1.0  # 0.0 to 1.0


@dataclass
class FunctionAnalysis:
    """Complete type analysis for a function."""
    function: Callable
    parameters: Dict[str, TypeAnalysis]
    return_type: Optional[type] = None
    complexity_score: int = 1  # 1=simple, 5=very complex


class RightTyper:
    """Advanced type analyzer that determines optimal testing strategies."""

    def __init__(self):
        self.log = get_logger()
        self.type_registry = self._build_type_registry()
        self.constraint_patterns = self._build_constraint_patterns()

    def _build_type_registry(self) -> Dict[type, Callable[[], st.SearchStrategy]]:
        """Build registry of type-to-strategy mappings."""
        return {
            # Basic types
            int: lambda: st.integers(min_value=-100, max_value=100),
            float: lambda: st.floats(
                min_value=-100, max_value=100,
                allow_nan=False, allow_infinity=False
            ),
            str: lambda: st.text(max_size=20),
            bool: lambda: st.booleans(),
            bytes: lambda: st.binary(max_size=50),

            # Advanced numeric types
            complex: lambda: st.complex_numbers(
                min_magnitude=0, max_magnitude=100
            ),
            Decimal: lambda: st.decimals(
                min_value=-100, max_value=100,
                allow_nan=False, allow_infinity=False
            ),

            # Date/time types
            datetime: lambda: st.datetimes(
                min_value=datetime(2020, 1, 1),
                max_value=datetime(2025, 12, 31)
            ),
            date: lambda: st.dates(
                min_value=date(2020, 1, 1),
                max_value=date(2025, 12, 31)
            ),
            time: lambda: st.times(),
        }

    def _build_constraint_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Build patterns for detecting constraints from parameter names."""
        return {
            # Size/length indicators
            'size': {'type': int, 'min': 0, 'max': 1000},
            'length': {'type': int, 'min': 0, 'max': 1000},
            'count': {'type': int, 'min': 0, 'max': 100},
            'capacity': {'type': int, 'min': 1, 'max': 10000},

            # Index indicators
            'index': {'type': int, 'min': 0, 'max': 100},
            'idx': {'type': int, 'min': 0, 'max': 100},
            'position': {'type': int, 'min': 0, 'max': 100},
            'pos': {'type': int, 'min': 0, 'max': 100},

            # Range indicators
            'start': {'type': int, 'min': 0, 'max': 100},
            'end': {'type': int, 'min': 1, 'max': 101},
            'begin': {'type': int, 'min': 0, 'max': 100},
            'stop': {'type': int, 'min': 1, 'max': 101},

            # Percentage/ratio
            'percent': {'type': float, 'min': 0.0, 'max': 100.0},
            'percentage': {'type': float, 'min': 0.0, 'max': 100.0},
            'ratio': {'type': float, 'min': 0.0, 'max': 1.0},
            'rate': {'type': float, 'min': 0.0, 'max': 1.0},

            # String patterns
            'name': {'type': str, 'pattern': r'^[a-zA-Z][a-zA-Z0-9_]*$'},
            'email': {'type': str, 'pattern': 
                      r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'},
            'url': {'type': str, 'pattern': r'^https?://'},
            'path': {'type': str, 'pattern': r'^[/a-zA-Z0-9._-]+$'},
            'filename': {'type': str, 'pattern': r'^[a-zA-Z0-9._-]+$'},
        }

    def analyze_function(self, func: Callable) -> FunctionAnalysis:
        """Perform comprehensive type analysis on a function."""
        self.log.debug(f"[RightTyper] Analyzing function: {func.__name__}")

        sig = inspect.signature(func)
        parameters = {}
        complexity_score = 1

        for param_name, param in sig.parameters.items():
            analysis = self._analyze_parameter(param_name, param)
            parameters[param_name] = analysis
            complexity_score += self._calculate_param_complexity(analysis)

        return_type = self._extract_return_type(sig)

        return FunctionAnalysis(
            function=func,
            parameters=parameters,
            return_type=return_type,
            complexity_score=min(complexity_score, 5)
        )

    def _analyze_parameter(self, param_name: 
                           str, param: inspect.Parameter) -> TypeAnalysis:
        """Analyze a single parameter for type information."""
        primary_type = self._extract_primary_type(param)
        nullable = self._is_nullable(param.annotation)
        constraints = self._detect_constraints(param_name, primary_type)
        suggested_strategy = self._create_strategy(primary_type, constraints)
        confidence = self._calculate_confidence(param, primary_type)

        return TypeAnalysis(
            param_name=param_name,
            primary_type=primary_type,
            nullable=nullable,
            constraints=constraints,
            suggested_strategy=suggested_strategy,
            confidence=confidence
        )

    def _extract_primary_type(self, param: inspect.Parameter) -> type:
        """Extract the primary type from parameter annotation."""
        if param.annotation is inspect._empty:
            # Try to infer from default value
            if param.default is not inspect._empty and param.default is not None:
                return type(param.default)
            return Any

        annotation = param.annotation
        origin = get_origin(annotation)
        args = get_args(annotation)

        # Handle Union types (including Optional)
        if origin is Union:
            non_none_types = [arg for arg in args if arg is not type(None)]
            if non_none_types:
                return non_none_types[0]  # Take first non-None type

        # Handle generic types
        if origin is not None:
            return origin

        return annotation

    def _is_nullable(self, annotation) -> bool:
        """Check if parameter can be None."""
        if annotation is inspect._empty:
            return False

        origin = get_origin(annotation)
        args = get_args(annotation)

        if origin is Union:
            return type(None) in args

        return False

    def _detect_constraints(self, param_name: str, primary_type: type) -> Dict[str, Any]:
        """Detect constraints based on parameter name and type."""
        constraints = {}
        param_lower = param_name.lower()

        # Check against constraint patterns
        for pattern, constraint_info in self.constraint_patterns.items():
            if pattern in param_lower:
                if primary_type == constraint_info['type'] or primary_type is Any:
                    constraints.update(constraint_info)
                    break

        # Additional heuristics
        if primary_type == str:
            if any(word in param_lower for word in ['id', 'key', 'token']):
                constraints.update({'min_size': 5, 'max_size': 50})
            elif any(word in param_lower for word in ['description', 'comment', 'text']):
                constraints.update({'min_size': 10, 'max_size': 200})

        return constraints

    def _create_strategy(self, primary_type: type, constraints: Dict[str, Any]) -> st.SearchStrategy:
        """Create a Hypothesis strategy based on type and constraints."""
        base_strategy = None

        # Get base strategy from registry
        if primary_type in self.type_registry:
            base_strategy = self.type_registry[primary_type]()
        else:
            # Fallback to hypothesis from_type
            try:
                base_strategy = st.from_type(primary_type)
            except Exception:
                base_strategy = st.integers()  # Ultimate fallback

        # Apply constraints
        if constraints:
            base_strategy = self._apply_constraints(base_strategy, primary_type, constraints)

        return base_strategy

    def _apply_constraints(self, strategy: st.SearchStrategy, type_: type, constraints: Dict[str, Any]) -> st.SearchStrategy:
        """Apply constraints to a base strategy."""
        try:
            if type_ == int:
                min_val = constraints.get('min', -100)
                max_val = constraints.get('max', 100)
                return st.integers(min_value=min_val, max_value=max_val)

            elif type_ == float:
                min_val = constraints.get('min', -100.0)
                max_val = constraints.get('max', 100.0)
                return st.floats(min_value=min_val, max_value=max_val, allow_nan=False, allow_infinity=False)

            elif type_ == str:
                min_size = constraints.get('min_size', 0)
                max_size = constraints.get('max_size', 20)
                pattern = constraints.get('pattern')

                if pattern:
                    return st.from_regex(pattern, fullmatch=True)
                else:
                    return st.text(min_size=min_size, max_size=max_size)

            return strategy
        except Exception:
            return strategy

    def _calculate_param_complexity(self, analysis: TypeAnalysis) -> int:
        """Calculate complexity score for a parameter."""
        score = 0

        if analysis.primary_type in [list, dict, set, tuple]:
            score += 1
        if analysis.nullable:
            score += 1
        if analysis.constraints:
            score += len(analysis.constraints) // 2
        if analysis.confidence < 0.8:
            score += 1

        return score

    def _calculate_confidence(self, param: inspect.Parameter, primary_type: type) -> float:
        """Calculate confidence in type analysis."""
        confidence = 1.0

        if param.annotation is inspect._empty:
            confidence -= 0.3
        if primary_type is Any:
            confidence -= 0.4
        if param.default is inspect._empty:
            confidence -= 0.1

        return max(confidence, 0.0)

    def _extract_return_type(self, sig: inspect.Signature) -> Optional[type]:
        """Extract return type from signature."""
        if sig.return_annotation is inspect._empty:
            return None

        annotation = sig.return_annotation
        origin = get_origin(annotation)

        if origin is Union:
            args = get_args(annotation)
            non_none_types = [arg for arg in args if arg is not type(None)]
            if non_none_types:
                return non_none_types[0]

        return annotation if origin is None else origin

    def get_optimal_strategy(self, func: Callable) -> StrategyPlan:
        """Get optimal testing strategy for a function."""
        analysis = self.analyze_function(func)
        strategies = []

        for param_name, param_analysis in analysis.parameters.items():
            strategy = param_analysis.suggested_strategy
            if strategy is not None:
                if param_analysis.nullable:
                    strategy = st.none() | strategy
                strategies.append(strategy)
            else:
                # Fallback
                strategies.append(st.integers())

        return StrategyPlan(
            arg_strategy=st.tuples(*strategies) if strategies else st.tuples()
        )