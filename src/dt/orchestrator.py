from .contracts import RunConfig, TargetPair, LoggerMode, EqOptions
from .diffpairer import DiffPairer
from .strategies import StrategySynthesizer
from .harness import HarnessBuilder
from .abrunner import ABRunner
from .results import ResultCollector
from .logger import Logger
from .comparator import ABComparator
from . import logger


class Orchestrator:
    def __init__(self, log_mode: LoggerMode = LoggerMode.Normal, eq: EqOptions | None=None):
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
    ):

        # Get Target Pairs
        target = TargetPair(
            file_a=file_a, file_b=file_b, func_name=func_name
        )
        fn_a, fn_b = self.harness.build(target)

        # Generate strategy plan
        plan = self.strategy.create_strategy(fn_a)
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
