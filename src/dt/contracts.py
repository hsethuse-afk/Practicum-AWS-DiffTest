from dataclasses import dataclass
from typing import Callable, Any, Dict, List, Tuple
from enum import IntEnum


@dataclass
class TargetPair:
    file_a: Callable
    file_b: Callable
    func_name: str


@dataclass
class StrategyPlan:
    # Hypothesis strategy that yields a tuple of call args
    arg_strategy: Any


@dataclass
class RunConfig:
    max_examples: int = 200
    seed: int | None = None


@dataclass
class RunResult:
    input: Any
    output: Any


@dataclass
class CompareResult:
    equal: bool
    reason: str | None = None
    example: Tuple | None = None  # one illustrative failing input
    stats: Dict[str, int] | None = None
    mismatches: List[Dict[str, Any]] | None = (
        None  # small preview of failures
    )


@dataclass
class TestResult:
    target: TargetPair
    passed: bool
    detail: Dict[str, Any]


@dataclass
class LoggerMode(IntEnum):
    Silent = 1
    Normal = 2
    Verbose = 3
    Debug = 4

@dataclass
class EqOptions:
    rel_tol: float = 1e-9
    abs_tol: float = 0.0
    treat_nan_equal: bool = True
    compare_exceptions_by: str = "type"  # "type" or "full"
    allow_graceful_differences: bool = True  # Allow exception vs graceful return equivalence


@dataclass
class TypeConstraint:
    """Constraint information for a parameter type."""
    type_: type
    min_value: Any = None
    max_value: Any = None
    pattern: str = None
    allowed_values: List[Any] = None