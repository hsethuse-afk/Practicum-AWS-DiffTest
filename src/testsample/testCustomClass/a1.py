"""
Implementation A - Custom class differential testing example
"""

from typing import List


class Point:
    """A point in 2D space."""

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def distance_to(self, other: 'Point') -> float:
        """Calculate Euclidean distance to another point."""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    def __repr__(self) -> str:
        return f"Point({self.x}, {self.y})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Point):
            return False
        return abs(self.x - other.x) < 1e-9 and abs(self.y - other.y) < 1e-9


def find_closest_points(points: List[Point], threshold: float) -> List[tuple[Point, Point]]:
    """
    Find all pairs of points that are closer than the threshold distance.

    Args:
        points: List of Point objects
        threshold: Maximum distance threshold

    Returns:
        List of tuples containing pairs of close points

    Example:
        >>> p1 = Point(0, 0)
        >>> p2 = Point(1, 1)
        >>> p3 = Point(10, 10)
        >>> result = find_closest_points([p1, p2, p3], 2.0)
        >>> len(result)
        1
    """
    close_pairs = []

    # Implementation A: Using nested loops
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            distance = points[i].distance_to(points[j])
            if distance < threshold:
                close_pairs.append((points[i], points[j]))

    return close_pairs


def calculate_centroid(points: List[Point]) -> Point:
    """
    Calculate the centroid (center point) of a list of points.

    Args:
        points: List of Point objects

    Returns:
        Point representing the centroid

    Example:
        >>> p1 = Point(0, 0)
        >>> p2 = Point(2, 2)
        >>> centroid = calculate_centroid([p1, p2])
        >>> centroid.x
        1.0
        >>> centroid.y
        1.0
    """
    if not points:
        return Point(0, 0)

    # Sum all coordinates
    total_x = 0.0
    total_y = 0.0
    for point in points:
        total_x += point.x
        total_y += point.y

    # Calculate average
    n = len(points)
    return Point(total_x / n, total_y / n)
