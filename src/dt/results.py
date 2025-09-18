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
                "example": cmp.example,
                "stats": cmp.stats,
                "mismatches": cmp.mismatches,
            },
        )

    @staticmethod
    def print(run: RunResult):
        t = run.target
        stats = run.detail.get("stats") or {}
        if run.passed:
            print(
                f"✅ {t.func_name}({t.file_a} vs {t.file_b}): no difference found"
            )
        else:
            print(
                f"❌ {t.func_name}({t.file_a} vs {t.file_b}): {run.detail.get('reason')}"
            )
            mm = run.detail.get("mismatches") or []
            for i, m in enumerate(mm[:5], 1):  # brief preview
                print(
                    f"  #{i} args={m['args']}  A={m['A']}  B={m['B']}"
                )
            if len(mm) > 5:
                print(f"  ... and {len(mm) - 5} more mismatches.")
        if stats:
            print(
                f"Summary: total={stats.get('total_examples',0)}, "
                f"successes={stats.get('successes',0)}, "
                f"mismatches={stats.get('mismatches',0)}"
            )
