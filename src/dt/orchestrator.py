from .contracts import RunConfig, TargetPair
from .diffpairer import DiffPairer
from .strategies import StrategySynthesizer
from .harness import HarnessBuilder
from .abrunner import ABRunner
from .results import ResultCollector


class Orchestrator:
    def __init__(self):
        self.harness = HarnessBuilder()
        self.strategy = StrategySynthesizer()
        self.runner = ABRunner()
        self.results = ResultCollector()

    def run_pair(
        self,
        file_a: str,
        file_b: str,
        func_name: str,
        max_examples: int = 200,
    ):
        target = TargetPair(
            file_a=file_a, file_b=file_b, func_name=func_name
        )
        fn_a, fn_b = self.harness.build(target)
        plan = self.strategy.create_strategy(fn_a)
        print(f"✅ Test Startegies Successfully Generated:\n{plan}")
        cmp = self.runner.execute(
            fn_a, fn_b, plan, RunConfig(max_examples=max_examples)
        )
        out = self.results.collect(target, cmp)
        self.results.print(out)
        return out
