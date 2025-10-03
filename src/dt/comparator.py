from typing import Any, Dict, List
from math import isclose, isnan
from decimal import Decimal
from datetime import datetime, date, time

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


def is_graceful_difference(exc_val: Any, ret_val: Any, input_args: Any) -> bool:
    """Check if exception vs return represents a graceful/robust difference."""
    exc_str = str(exc_val) if exc_val else ""

    # Empty container handling: ZeroDivisionError vs 0.0/0/empty result
    if "ZeroDivisionError" in exc_str or "division by zero" in exc_str:
        # Check if input suggests empty container operation
        if input_args and isinstance(input_args, (tuple, list)):
            for arg in input_args:
                if isinstance(arg, (list, tuple, str)) and len(arg) == 0:
                    # Return value should be a reasonable empty/zero default
                    if ret_val in [0, 0.0, "", [], (), {}]:
                        return True
                    # Or return value is mathematically sensible for empty input
                    if isinstance(ret_val, (int, float)) and ret_val == 0:
                        return True

    # KeyError vs ValueError for invalid input (both indicate input validation)
    if ("KeyError" in exc_str and "ValueError" in str(type(ret_val).__name__)) or \
       ("ValueError" in exc_str and "KeyError" in str(type(ret_val).__name__)):
        return False  # These are different error types, keep as mismatch

    # IndexError vs None/empty for out-of-bounds access
    if "IndexError" in exc_str and ret_val is None:
        return True

    # Add more patterns as needed
    return False


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

    # Cross numeric types (int, float, Decimal)
    if isinstance(a, (int, float, Decimal)) and isinstance(b, (int, float, Decimal)):
        # Handle Decimal with special care
        if isinstance(a, Decimal) or isinstance(b, Decimal):
            try:
                decimal_a = Decimal(str(a)) if not isinstance(a, Decimal) else a
                decimal_b = Decimal(str(b)) if not isinstance(b, Decimal) else b
                abs_tol_decimal = Decimal(str(_abs_tol(opt)))
                rel_tol_decimal = Decimal(str(opt.rel_tol))

                diff = abs(decimal_a - decimal_b)
                if diff <= abs_tol_decimal:
                    return True
                if max(abs(decimal_a), abs(decimal_b)) > 0:
                    return diff / max(abs(decimal_a), abs(decimal_b)) <= rel_tol_decimal
                return True
            except Exception:
                return False

        # Regular numeric comparison
        if isinstance(a, float) and isinstance(b, float):
            if opt.treat_nan_equal and isnan(a) and isnan(b):
                return True
        return isclose(float(a), float(b), rel_tol=opt.rel_tol, abs_tol=_abs_tol(opt))

    # Complex numbers
    if isinstance(a, complex) and isinstance(b, complex):
        return (
            isclose(a.real, b.real, rel_tol=opt.rel_tol, abs_tol=_abs_tol(opt)) and
            isclose(a.imag, b.imag, rel_tol=opt.rel_tol, abs_tol=_abs_tol(opt))
        )

    # Date/time types
    if isinstance(a, (datetime, date, time)) and isinstance(b, type(a)):
        return a == b

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
                        # One raised, the other returned - check for graceful differences
                        if eq.allow_graceful_differences:
                            if a_tag == "exc" and b_tag == "ret":
                                # A crashed, B returned gracefully
                                local_success = is_graceful_difference(a_val, b_val, a_result.input)
                            elif b_tag == "exc" and a_tag == "ret":
                                # B crashed, A returned gracefully
                                local_success = is_graceful_difference(b_val, a_val, b_result.input)
                            else:
                                local_success = False
                        else:
                            # Strict mode: exception vs return is always a mismatch
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
