from dataclasses import dataclass
from typing import Callable, Any, Dict, List, Tuple


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
class CompareResult:
    equal: bool
    reason: str | None = None
    example: Tuple | None = None  # one illustrative failing input
    stats: Dict[str, int] | None = None
    mismatches: List[Dict[str, Any]] | None = (
        None  # small preview of failures
    )


@dataclass
class RunResult:
    target: TargetPair
    passed: bool
    detail: Dict[str, Any]
