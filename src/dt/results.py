from typing import List, Dict, Any
from .contracts import TargetPair, CompareResult, TestResult
from .logger import get_logger
import inspect


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
                "mismatches": cmp.mismatches,  # Complete list
                "matches": cmp.matches,  # Complete list
            },
            warnings=warnings,
        )

    @staticmethod
    def _format_instance(instance: Any) -> str:
        """
        Format an instance for display by showing its attributes.

        For class instances, extracts and displays the instance attributes
        instead of showing unhelpful <ClassName object at 0x...> output.
        """
        if not hasattr(instance, '__class__'):
            return repr(instance)

        cls = instance.__class__
        # Skip built-in types
        if cls.__module__ == 'builtins':
            return repr(instance)

        # Try to extract instance attributes
        try:
            # Get all non-private attributes
            attrs = {k: v for k, v in vars(instance).items() if not k.startswith('_')}

            if attrs:
                # Limit attribute values display for readability
                attrs_formatted = {}
                for k, v in attrs.items():
                    v_repr = repr(v)
                    # Truncate long representations
                    if len(v_repr) > 50:
                        v_repr = v_repr[:47] + '...'
                    attrs_formatted[k] = v_repr

                attrs_str = ', '.join(f'{k}={v}' for k, v in attrs_formatted.items())
                return f"{cls.__name__}({attrs_str})"
        except:
            pass

        # Fallback to class name
        return f"{cls.__name__}(...)"

    @staticmethod
    def _format_args(args: tuple, is_class_method: bool = False) -> str:
        """
        Format arguments for display.

        For class methods, the first argument is the instance which should be
        formatted specially to show constructor parameters.
        """
        if not args:
            return "()"

        if is_class_method and len(args) > 0:
            # First arg is the instance
            instance = args[0]
            method_args = args[1:]

            instance_str = ResultCollector._format_instance(instance)
            if method_args:
                method_args_str = ', '.join(repr(arg) for arg in method_args)
                return f"(instance={instance_str}, {method_args_str})"
            else:
                return f"(instance={instance_str})"
        else:
            # Regular function args
            return f"({', '.join(repr(arg) for arg in args)})"

    @staticmethod
    def print(run: TestResult):
        log = get_logger()
        t = run.target
        stats = run.detail.get("stats") or {}
        is_class_method = t.is_class_method

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
                # Format args nicely, especially for class methods
                args_str = ResultCollector._format_args(m['args'], is_class_method)
                log.normal(
                    f"  #{i} args={args_str}  A={m['A']}  B={m['B']}"
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
