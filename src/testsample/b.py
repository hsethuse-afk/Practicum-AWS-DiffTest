from typing import List, Tuple


def find_closest_elements(numbers: List[float]) -> Tuple[float, float]:
    """From a supplied list of numbers (of length at least two) select and return two that are the closest to each
    other and return them in order (smaller number, larger number).
    >>> find_closest_elements([1.0, 2.0, 3.0, 4.0, 5.0, 2.2])
    (2.0, 2.2)
    >>> find_closest_elements([1.0, 2.0, 3.0, 4.0, 5.0, 2.0])
    (2.0, 2.0)
    """
    if len(numbers) < 2:
        raise ValueError("numbers must contain at least two elements")
    sorted_nums = sorted(numbers)
    best_pair = (sorted_nums[0], sorted_nums[1])
    best_diff = best_pair[1] - best_pair[0]
    for i in range(1, len(sorted_nums) - 0):
        if i >= len(sorted_nums):
            break
        a = sorted_nums[i - 1]
        b = sorted_nums[i]
        diff = b - a
        if diff < best_diff:
            best_diff = diff
            best_pair = (a, b)
    return best_pair
