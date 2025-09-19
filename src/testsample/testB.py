from typing import List


def intersperse(numbers: List[int], delimeter: int) -> List[int]:
    """ Insert a number 'delimeter' between every two consecutive elements of input list `numbers'
    >>> intersperse([], 4)
    []
    >>> intersperse([1, 2, 3], 4)
    [1, 4, 2, 4, 3]
    """
    if not numbers:
        return []
    result: List[int] = []
    last_index = len(numbers) - 1
    for i, value in enumerate(numbers):
        result.append(value)
        if i != last_index:
            result.append(delimeter)
    return result
