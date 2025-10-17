def maximum(arr, k):
    """
    Given an array arr of integers and a integer k, return a sorted list 
    of length k with the maximum k numbers in arr.
    """
    if k == 0:
        return []
    arr.sort()
    ans = arr[-k:]
    return ans
