from typing import Any, Dict, List
from math import isclose, isnan

from .contracts import CompareResult, RunResult, EqOptions
from .logger import get_logger


# --- helpers ---------------------------------------------------------------

def _abs_tol(opt: EqOptions) -> float:
    """Support both EqOptions.abs_tol (preferred) and legacy abs_total."""
    return getattr(opt, "abs_tol", getattr(opt, "abs_total", 0.0))


def _parse_exc(s: str) -> tuple[str, str]:
    """Runner encodes exceptions as 'TypeName: message' → (type, message)."""
    if not isinstance(s, str):
        return ("", "")
    parts = s.split(":", 1)
    if len(parts) == 1:
        return (parts[0].strip(), "")
    return (parts[0].strip(), parts[1].strip())


def exception_equal(a: Any, b: Any, opt: EqOptions) -> bool:
    """Compare exceptions by type, or type+message based on policy."""
    ta, ma = _parse_exc(a if isinstance(a, str) else str(a))
    tb, mb = _parse_exc(b if isinstance(b, str) else str(b))
    if opt.compare_exceptions_by == "type":
        return ta == tb
    return ta == tb and ma == mb


def approx_equal(a: Any, b: Any, opt: EqOptions) -> bool:
    """Recursive, structure-aware equality with numeric tolerance and NaN policy."""
    # Fast path: identical object or strict equality
    if a is b or a == b:
        return True

    # Floats & NaNs
    if isinstance(a, float) and isinstance(b, float):
        if opt.treat_nan_equal and isnan(a) and isnan(b):
            return True
        return isclose(a, b, rel_tol=opt.rel_tol, abs_tol=_abs_tol(opt))

    # Cross numeric types (e.g., int vs float)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        # If both are floats, honor NaN==NaN policy
        if isinstance(a, float) and isinstance(b, float):
            if opt.treat_nan_equal and isnan(a) and isnan(b):
                return True
        return isclose(float(a), float(b), rel_tol=opt.rel_tol, abs_tol=_abs_tol(opt))

    # Tuple/List (same type & length)
    if isinstance(a, (list, tuple)) and isinstance(b, type(a)) and len(a) == len(b):
        return all(approx_equal(x, y, opt) for x, y in zip(a, b))

    # Sets (unordered)
    if isinstance(a, set) and isinstance(b, set):
        if a == b:
            return True
        if len(a) == len(b):
            # Tolerant membership match (sets have no duplicates)
            return all(any(approx_equal(x, y, opt) for y in b) for x in a)
        return False

    # Dicts (same keys)
    if isinstance(a, dict) and isinstance(b, dict) and a.keys() == b.keys():
        return all(approx_equal(a[k], b[k], opt) for k in a)

    # Bytes-like
    if isinstance(a, (bytes, bytearray)) and isinstance(b, type(a)):
        return a == b

    # Fallback strict equality
    return a == b


class ABComparator:
    def __init__(
        self,
        output_check: bool = True,
        input_check: bool = False,
        eq: EqOptions | None = None,
    ):
        self.output_check = output_check
        self.input_check = input_check
        self.eq = eq or EqOptions()
        self.log = get_logger()

    def compare(self, a_results: List[RunResult], 
                b_results: List[RunResult]) -> CompareResult:
        self.log.verbose("[ABComparator] Comparing Results")

        eq = self.eq
        mismatches: List[Dict[str, Any]] = []
        mismatches_count = 0
        successes = 0

        # Be tolerant to length mismatches; compare up to the shortest.
        total = min(len(a_results), len(b_results))

        for i in range(total):
            a_result = a_results[i]
            b_result = b_results[i]
            local_success = True

            # (Optional) input parity check hook
            if self.input_check:
                # Inputs are generated once and shared, so this is a no-op for now.
                pass

            if self.output_check:
                a_tag, a_val = a_result.output  # "ret" | "exc"
                b_tag, b_val = b_result.output

                if a_tag == "exc" or b_tag == "exc":
                    if a_tag == "exc" and b_tag == "exc":
                        # Both raised → compare exceptions per policy
                        local_success = exception_equal(a_val, b_val, eq)
                    else:
                        # One raised, the other returned
                        local_success = False
                else:
                    # Both returned → tolerant structural equality
                    local_success = approx_equal(a_val, b_val, eq)

            if not local_success:
                mismatches_count += 1
                mismatches.append(
                    {"args": a_result.input, "A": a_result.output, "B": b_result.output}
                )
            else:
                successes += 1

        # If one side produced extra results, count them as mismatches (rare)
        if len(a_results) != len(b_results):
            extra = abs(len(a_results) - len(b_results))
            mismatches_count += extra
            total += extra  # reflect in totals

        passed = mismatches_count == 0
        example = None if passed else (mismatches[0]["args"] if mismatches else None)
        reason = (
            "All examples matched under comparator policy."
            if passed
            else "Differences observed (see mismatches preview)."
        )

        stats = {
            "total_examples": total,
            "successes": successes,
            "mismatches": mismatches_count,
            # Surface active policy in stats (use canonical key name 'abs_tol')
            "rel_tol": eq.rel_tol,
            "abs_tol": _abs_tol(eq),
            "treat_nan_equal": eq.treat_nan_equal,
            "exc_mode": eq.compare_exceptions_by,
        }

        return CompareResult(
            equal=passed,
            reason=reason,
            example=example,
            stats=stats,
            mismatches=mismatches,
        )
