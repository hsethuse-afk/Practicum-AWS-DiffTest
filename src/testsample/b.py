def truncate_number(number: float) -> float:
    """ Given a positive floating point number, it can be decomposed into
    and integer part (largest integer smaller than given number) and decimals
    (leftover part always smaller than 1).

    Return the decimal part of the number.
    >>> truncate_number(3.5)
    0.5
    """
    import math
    # Use floor to get the integer part and subtract to get the fractional part.
    frac = number - math.floor(number)
    # Normalize -0.0 to 0.0
    if frac == 0.0:
        return 0.0
    return frac
