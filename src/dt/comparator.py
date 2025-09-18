from typing import Any, Tuple
from .contracts import CompareResult


def _safe_call(fn, args: tuple):
    try:
        return ("ret", fn(*args))
    except Exception as e:
        return ("exc", f"{type(e).__name__}: {e}")


def compare(fn_a, fn_b, args: tuple) -> CompareResult:
    out_a = _safe_call(fn_a, args)
    out_b = _safe_call(fn_b, args)
    if out_a == out_b:
        return CompareResult(equal=True)
    return CompareResult(
        equal=False,
        reason=f"Mismatch A={out_a} vs B={out_b}",
        example=args,
    )
