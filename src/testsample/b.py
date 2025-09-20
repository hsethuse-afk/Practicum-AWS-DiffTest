def find_zero(xs: list):
    """ xs are coefficients of a polynomial.
    find_zero find x such that poly(x) = 0.
    find_zero returns only only zero point, even if there are many.
    Moreover, find_zero only takes list xs having even number of coefficients
    and largest non zero coefficient as it guarantees
    a solution.
    >>> round(find_zero([1, 2]), 2) # f(x) = 1 + 2x
    -0.5
    >>> round(find_zero([-6, 11, -6, 1]), 2) # (x - 1) * (x - 2) * (x - 3) = -6 + 11x - 6x^2 + x^3
    1.0
    """
    # make a copy and trim trailing zeros (if any) to determine actual degree
    coeffs = list(xs)
    while len(coeffs) > 1 and coeffs[-1] == 0:
        coeffs.pop()
    if not coeffs:
        raise ValueError("Coefficient list is empty or all zeros; infinite roots.")
    # quick check for exact zero at 0
    def f(x):
        return poly(coeffs, x)
    if abs(f(0.0)) == 0.0:
        return 0.0
    # Start with symmetric interval and expand until we find a sign change.
    a, b = -1.0, 1.0
    fa, fb = f(a), f(b)
    # treat near-zero values as zero
    eps_f = 1e-15
    if abs(fa) < eps_f:
        return float(a)
    if abs(fb) < eps_f:
        return float(b)
    max_expand_iters = 200
    it = 0
    while fa * fb > 0 and it < max_expand_iters:
        # expand interval exponentially outward
        a *= 2.0
        b *= 2.0
        fa = f(a)
        fb = f(b)
        if abs(fa) < eps_f:
            return float(a)
        if abs(fb) < eps_f:
            return float(b)
        it += 1
    if fa * fb > 0:
        # fallback: try asymmetric expansion if symmetric didn't find sign change
        a, b = -1.0, 1.0
        fa, fb = f(a), f(b)
        for k in range(1, max_expand_iters):
            # expand one side at a time
            if abs(fa) < eps_f:
                return float(a)
            if abs(fb) < eps_f:
                return float(b)
            if k % 2 == 1:
                a *= 2.0
                fa = f(a)
            else:
                b *= 2.0
                fb = f(b)
            if fa * fb <= 0:
                break
        if fa * fb > 0:
            # As a last resort, attempt Newton's method from 0.0
            # compute derivative via finite differences
            x = 0.0
            for _ in range(200):
                fx = f(x)
                if abs(fx) < 1e-14:
                    return float(x)
                h = 1e-8 if abs(x) < 1.0 else 1e-8 * abs(x)
                d = (f(x + h) - f(x - h)) / (2 * h)
                if d == 0 or d != d:  # avoid division by zero or NaN
                    break
                x = x - fx / d
            return float(x)
    # Now we have bracket [a, b] with fa*fb <= 0
    # Bisection method
    left, right = a, b
    fl, fr = fa, fb
    if abs(fl) < eps_f:
        return float(left)
    if abs(fr) < eps_f:
        return float(right)
    tol = 1e-12
    max_bisect = 200
    for _ in range(max_bisect):
        mid = (left + right) / 2.0
        fm = f(mid)
        if abs(fm) < 1e-14:
            return float(mid)
        # stop if interval is sufficiently small
        if abs(right - left) <= tol * max(1.0, abs(left), abs(right)):
            return float(mid)
        if fl * fm <= 0:
            right, fr = mid, fm
        else:
            left, fl = mid, fm
    # return midpoint if max iterations reached
    return float((left + right) / 2.0)
