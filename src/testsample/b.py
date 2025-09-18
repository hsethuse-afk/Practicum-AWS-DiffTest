# GPT-5-mini code
from typing import List


def has_close_elements(numbers: List[float], threshold: float) -> bool:
    """Check if in given list of numbers, are any two numbers closer to each other than
    given threshold.
    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)
    False
    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)
    True
    """
    if threshold <= 0.0:
        return False
    n = len(numbers)
    if n < 2:
        return False
    nums = sorted(numbers)
    prev = nums[0]
    for x in nums[1:]:
        if x - prev < threshold:
            return True
        prev = x
    return False
