from .contracts import RunConfig, TargetPair, LoggerMode
from .diffpairer import DiffPairer
from .strategy.strategies import StrategySynthesizer
from .harness import HarnessBuilder
from .abrunner import ABRunner
from .results import ResultCollector
from .logger import Logger
from .comparator import ABComparator
from . import logger


class Orchestrator:
    def __init__(self, log_mode: LoggerMode = LoggerMode.Normal):
        logger.set_logger(Logger(log_mode))
        self.log = logger.get_logger()
        self.harness = HarnessBuilder()
        self.strategy = StrategySynthesizer()
        self.runner = ABRunner()
        self.comparator = ABComparator()
        self.results = ResultCollector()

    def run_pair(
        self,
        file_a: str,
        file_b: str,
        func_name: str,
        max_examples: int = 200,
        test_file: str = None,
    ):
        """
        Run differential testing on a pair of functions.

        Args:
            file_a: Path to first file
            file_b: Path to second file
            func_name: Name of the function to test
            max_examples: Maximum number of test examples
            test_file: Optional path to test file for RightTyper type inference
                      (e.g., "test.py") that will be used if annotations are missing
        """

        # Get Target Pairs
        target = TargetPair(
            file_a=file_a, file_b=file_b, func_name=func_name
        )
        fn_a, fn_b = self.harness.build(target)

        # Validate test file if provided
        if test_file:
            import os

            if not os.path.exists(test_file):
                self.log.debug(
                    f"[Orchestrator] Test file not found: {test_file}"
                )
                test_file = None
            else:
                self.log.verbose(
                    f"[Orchestrator] Using test file for type inference: {test_file}"
                )

        # Generate strategy plan (with optional test file for type inference)
        plan = self.strategy.create_strategy(fn_a, test_file=test_file)
        self.log.verbose(
            f"✅ Test Startegies Successfully Generated:\n{plan}"
        )

        # Run and Compare
        a_results, b_results = self.runner.execute(
            fn_a, fn_b, plan, RunConfig(max_examples=max_examples)
        )
        cmp = self.comparator.compare(a_results, b_results)
        out = self.results.collect(target, cmp)
        self.results.print(out)

        return out
