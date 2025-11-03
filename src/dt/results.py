from typing import List, Dict, Any
from .contracts import TargetPair, CompareResult, TestResult
from .logger import get_logger


class ResultCollector:

    def collect(
        self,
        target: TargetPair,
        cmp: CompareResult,
        warnings: List[Dict[str, Any]] | None = None,
    ) -> TestResult:
        return TestResult(
            target=target,
            passed=cmp.equal,
            detail={
                "reason": cmp.reason,
                "example": cmp.example,
                "stats": cmp.stats,
                "mismatches": cmp.mismatches,
            },
            warnings=warnings,
        )

    @staticmethod
    def print(run: TestResult):
        log = get_logger()
        t = run.target
        stats = run.detail.get("stats") or {}
        if run.passed:
            log.normal(
                f"{t.func_name}({t.file_a} vs {t.file_b}): no difference found"
            )
        else:
            log.normal(
                f"{t.func_name}({t.file_a} vs {t.file_b}): {run.detail.get('reason')}"
            )
            mm = run.detail.get("mismatches") or []
            for i, m in enumerate(mm[:5], 1):  # brief preview
                log.normal(
                    f"  #{i} args={m['args']}  A={m['A']}  B={m['B']}"
                )
            if len(mm) > 5:
                log.normal(f"  ... and {len(mm) - 5} more mismatches.")
        if stats:
            log.normal(
                f"Summary: total={stats.get('total_examples',0)}, "
                f"successes={stats.get('successes',0)}, "
                f"mismatches={stats.get('mismatches',0)}"
            )

        # Display captured warnings if any
        if run.warnings:
            # Deduplicate warnings by (message, category, filename, lineno)
            unique_warnings = []
            seen = set()
            for w in run.warnings:
                key = (
                    w["message"],
                    w["category"],
                    w["filename"],
                    w["lineno"],
                )
                if key not in seen:
                    seen.add(key)
                    unique_warnings.append(w)

            if unique_warnings:
                log.normal(
                    f"\n⚠️  Warnings captured during execution ({len(unique_warnings)} unique):"
                )
                for w in unique_warnings:
                    log.normal(
                        f"  {w['filename']}:{w['lineno']}: {w['category']}: {w['message']}"
                    )
