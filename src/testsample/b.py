<<<<<<< HEAD
def maximum(arr, k):
    """
    Given an array arr of integers and a integer k, return a sorted list 
    of length k with the maximum k numbers in arr.
    """
    if k <= 0:
        return []
    s = sorted(arr)
    if k >= len(s):
        return s
    return s[-k:]
=======
def make_a_pile(n):
    """
    Given a positive integer n, you have to make a pile of n levels of stones.
    The first level has n stones.
    The number of stones in the next level is:
        - the next odd number if n is odd.
        - the next even number if n is even.
    Return the number of stones in each level in a list, where element at index
    i represents the number of stones in the level (i+1).
    """
    if n <= 0:
        return []
    return [n + 2 * i for i in range(n)]
>>>>>>> Mingkai-WIP
