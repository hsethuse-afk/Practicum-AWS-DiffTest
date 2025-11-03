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
    # Individual parameter strategies for serialization (param_name -> strategy)
    param_strategies: Dict[str, Any] = None


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
    warnings: List[Dict[str, Any]] | None = None  # captured warnings during execution


@dataclass
class LoggerMode(IntEnum):
    Silent = 1
    Normal = 2
    Verbose = 3
    Debug = 4
