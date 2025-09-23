from typing import Any, Dict, List
from .contracts import CompareResult, RunResult, EqOptions
from math import isclose, isnan
from .logger import get_logger

def _parse_exec(s: str) -> tuple[str, str]:
    """
    Runner encodes exceptions as 'TypeName: message'.
    Return (type_name, message) with message possibly empty.
    """
    if not isinstance(s, str):
        return("", "")
    parts = s.split(":", 1)
    if len(parts) == 1:
        return (parts[0].strip(), "")
    return (parts[0].strip(), parts[1].strip())

def exception_equal(a: Any, b: Any, opt: EqOptions) -> bool:
    ta, ma = _parse_exec(a if isinstance(a, str) else str(a))
    tb, mb = _parse_exec(b if isinstance(b, str) else str(b))
    if opt.compare_exceptions_by == "type":
        return ta == tb
    return ta == tb and ma == mb

def approx_equal(a: Any, b: Any, opt: EqOptions) -> bool:
    # Identical object or direct equality covers non-numerics fast
    if a is b or a == b:
        return True

    # Floats & NaNs
    if isinstance(a, float) and isinstance(b, float):
        if opt.treat_nan_equal and isnan(a) and isnan(b):
            return True
        return isclose(a, b, rel_tol=opt.rel_tol, abs_tol=opt.abs_tol)

    # Simple numeric cross-types (e.g., int vs float)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        # Handle NaN on b if float
        if isinstance(a, float) and isinstance(b, float):
            if opt.treat_nan_equal and isnan(a) and isnan(b):
                return True
        return isclose(float(a), float(b), rel_tol=opt.rel_tol, abs_tol=opt.abs_tol)

    # Tuples / Lists (same type + same length)
    if isinstance(a, (list, tuple)) and isinstance(b, type(a)) and len(a) == len(b):
        return all(approx_equal(x, y, opt) for x, y in zip(a, b))

    # Sets
    if isinstance(a, set) and isinstance(b, set):
        # set equality is unordered by nature
        if a == b:
            return True
        # As a fallback for float tolerance inside sets, compare via 
        # multiset-ish check
        if len(a) == len(b):
            return all(any(approx_equal(x, y, opt) for y in b) for x in a)
        return False

    # Dicts  handling of same keys
    if isinstance(a, dict) and isinstance(b, dict) and a.keys() == b.keys():
        return all(approx_equal(a[k], b[k], opt) for k in a)

    # Bytes/bytearray (exact)
    if isinstance(a, (bytes, bytearray)) and isinstance(b, type(a)):
        return a == b

    # Fallback strict
    return a == b

class ABComparator:
    def __init__(self, output_check: bool= True, input_check: bool = False, 
                 eq: EqOptions | None = None):
        self.output_check = output_check
        self.input_check = input_check
        self.eq = eq or EqOptions()
        self.log = get_logger()

    def compare(
        self, a_results: RunResult, b_results: RunResult
    ) -> CompareResult:
        self.log.verbose("[ABComparator] Comparing Results")
        eq = getattr(self, "eq", EqOptions())

        mismatches: List[Dict[str, Any]] = []
        mismatches_count = 0
        successes = 0
        total = len(a_results)

        for i in range(total):
            a_result: RunResult = a_results[i]
            b_result: RunResult = b_results[i]
            local_success = True
            
            if self.input_check:
                # TODO - Add input parity checks here if we records inputs 
                # separately
                pass
            if self.output_check:
                a_tag, a_val = a_result.output #  "ret" | "exc", payload
                b_tag, b_val =b_result.output
               
                if a_tag == "exc" or b_tag == "exc":
                    if a_tag == "exc" and b_tag == "exc":
                        # both are raised -> comparing by policy ("type or type and msg")
                        local_success = exception_equal(a_val, b_val, eq)
                    else:
                        # one raised and the other returned
                        local_success = False
                else:
                    # b0th returned -> use recursive structural approx equality
                    local_success = approx_equal(a_val, b_val, eq)

            if not local_success:
                mismatches_count +=1
                mismatches.append(
                    {"args": a_result.input, "A": a_result.output, "B": b_result.output}
                )
            else:
                successes += 1

        passed = mismatches_count == 0
        # Pick one illustrative example if any
        example = None if passed else (mismatches[0]["args"] if mismatches else None)
        reason = (
            "All examples matched under comp policy"
            if passed
            else "Differences observed (see mismatches preview)."
        )
        stats = {
            "total_examples": total,
            "successes": successes,
            "mismatches": mismatches_count,
            "rel_tol": eq.rel_tol,
            "abs_tol": eq.abs_total,
            "treat_nan_equal": eq.treat_nan_equal,
            "exc mode": eq.compare_exceptions_by,
        }

        return CompareResult(
            equal=passed,
            reason=reason,
            example=example,
            stats= stats,
            mismatches=mismatches,
        )
