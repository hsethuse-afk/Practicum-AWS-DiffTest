"""
Implementation B - Custom class differential testing example
Non-functional changes from Implementation A
"""


class Point:
    """A point in 2D space."""

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def distance_to(self, other):
        """Calculate Euclidean distance to another point."""
        dx = self.x - other.x
        dy = self.y - other.y
        return (dx * dx + dy * dy) ** 0.5

    def __repr__(self):
        return f"Point({self.x}, {self.y})"

    def __eq__(self, other):
        if not isinstance(other, Point):
            return False
        return (
            abs(self.x - other.x) < 1e-9
            and abs(self.y - other.y) < 1e-9
        )


def find_closest_points(points, threshold):
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
    result = []

    # Implementation B: Using enumerate (non-functional change)
    for idx, point1 in enumerate(points):
        for point2 in points[idx + 1 :]:
            dist = point1.distance_to(point2)
            if dist < threshold:
                result.append((point1, point2))

    return result


def calculate_centroid(points):
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

    # Different variable names and order (non-functional change)
    sum_x = sum(p.x for p in points)
    sum_y = sum(p.y for p in points)

    count = len(points)
    avg_x = sum_x / count
    avg_y = sum_y / count

    return Point(avg_x, avg_y)
