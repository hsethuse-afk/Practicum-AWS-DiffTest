from .contracts import TargetPair, CompareResult, RunResult


class ResultCollector:
    def collect(
        self, target: TargetPair, cmp: CompareResult
    ) -> RunResult:
        return RunResult(
            target=target,
            passed=cmp.equal,
            detail={
                "reason": cmp.reason,
                "example": getattr(cmp, "example", None),
            },
        )

    @staticmethod
    def print(run: RunResult):
        t = run.target
        if run.passed:
            print(
                f"✅ {t.func_name}({t.file_a} vs {t.file_b}): no difference found"
            )
        else:
            print(
                f"❌ {t.func_name}({t.file_a} vs {t.file_b}): {run.detail.get('reason')}"
            )
            ex = run.detail.get("example")
            if ex is not None:
                print(f"   example: {ex}")
