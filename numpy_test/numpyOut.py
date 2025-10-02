import numpy as np


# def square_elements(arr: np.ndarray) -> np.ndarray:
def square_elements(arr):
    """
    Returns a new array where each element is squared.
    """
    return np.square(arr)


# Example
print(square_elements(np.array([1, 2, 3, 4])))
# Output: [ 1  4  9 16]


def matmul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    # def matmul(a, b):
    """
    Performs matrix multiplication between two numpy arrays.
    """
    return np.matmul(a, b)


# Example
A = np.array([[1, 2], [3, 4]])
B = np.array([[2, 0], [1, 2]])
print(matmul(A, B))
# Output: [[ 4  4]
#          [10  8]]


# def max_with_index(arr: np.ndarray) -> tuple:
def max_with_index(arr):
    """
    Returns the maximum value in the array and its index.
    """
    idx = np.argmax(arr)
    return arr[idx], idx


# Example
print(max_with_index(np.array([10, 50, 20, 30])))
# Output: (50, 1)


# def normalize(arr: np.ndarray) -> np.ndarray:
def normalize(arr: np.ndarray) -> np.ndarray:
    """
    Normalizes an array to range [0, 1].
    """
    arr_min, arr_max = np.min(arr), np.max(arr)
    return (arr - arr_min) / (arr_max - arr_min)


# Example
print(normalize(np.array([2, 4, 6, 8])))
# Output: [0.   0.33 0.67 1.  ]


# def make_identity(n: int) -> np.ndarray:
def make_identity(n):
    """
    Returns an identity matrix of size n x n.
    """
    return np.eye(n)


# Example
print(make_identity(3))
# Output:
# [[1. 0. 0.]
#  [0. 1. 0.]
#  [0. 0. 1.]]


# def filter_even(arr: np.ndarray) -> np.ndarray:
def filter_even(arr):
    """
    Returns only even numbers from the array.
    """
    return arr[arr % 2 == 0]


# Example
print(filter_even(np.array([1, 2, 3, 4, 5, 6])))
# Output: [2 4 6]
