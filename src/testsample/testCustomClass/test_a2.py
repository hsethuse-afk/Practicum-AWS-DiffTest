"""
Unit tests for a2.py - Point class and related functions
"""

from a2 import Point, find_closest_points, calculate_centroid


def test_point_creation() -> None:
    """Test Point object creation."""
    p = Point(3.0, 4.0)
    assert p.x == 3.0
    assert p.y == 4.0


def test_point_distance() -> None:
    """Test distance calculation between two points."""
    p1 = Point(0, 0)
    p2 = Point(3, 4)
    assert p1.distance_to(p2) == 5.0

    p3 = Point(1, 1)
    p4 = Point(4, 5)
    assert p3.distance_to(p4) == 5.0


def test_point_equality() -> None:
    """Test Point equality comparison."""
    p1 = Point(1.0, 2.0)
    p2 = Point(1.0, 2.0)
    p3 = Point(1.0, 2.1)

    assert p1 == p2
    assert not (p1 == p3)


def test_find_closest_points_empty() -> None:
    """Test find_closest_points with empty list."""
    result = find_closest_points([], 5.0)
    assert result == []


def test_find_closest_points_single() -> None:
    """Test find_closest_points with single point."""
    p1 = Point(0, 0)
    result = find_closest_points([p1], 5.0)
    assert result == []


def test_find_closest_points_basic() -> None:
    """Test find_closest_points with basic case."""
    p1 = Point(0, 0)
    p2 = Point(1, 1)
    p3 = Point(10, 10)

    result = find_closest_points([p1, p2, p3], 2.0)
    assert len(result) == 1
    assert (p1, p2) in result


def test_find_closest_points_multiple_pairs() -> None:
    """Test find_closest_points with multiple close pairs."""
    p1 = Point(0, 0)
    p2 = Point(1, 0)
    p3 = Point(2, 0)
    p4 = Point(10, 10)

    result = find_closest_points([p1, p2, p3, p4], 1.5)
    assert len(result) == 2
    assert (p1, p2) in result
    assert (p2, p3) in result


def test_find_closest_points_no_matches() -> None:
    """Test find_closest_points with no close pairs."""
    p1 = Point(0, 0)
    p2 = Point(10, 10)
    p3 = Point(20, 20)

    result = find_closest_points([p1, p2, p3], 1.0)
    assert len(result) == 0


def test_calculate_centroid_empty() -> None:
    """Test calculate_centroid with empty list."""
    result = calculate_centroid([])
    assert result == Point(0, 0)


def test_calculate_centroid_single() -> None:
    """Test calculate_centroid with single point."""
    p1 = Point(5, 10)
    result = calculate_centroid([p1])
    assert result == p1


def test_calculate_centroid_two_points() -> None:
    """Test calculate_centroid with two points."""
    p1 = Point(0, 0)
    p2 = Point(2, 2)
    result = calculate_centroid([p1, p2])
    assert result.x == 1.0
    assert result.y == 1.0


def test_calculate_centroid_multiple_points() -> None:
    """Test calculate_centroid with multiple points."""
    p1 = Point(0, 0)
    p2 = Point(3, 0)
    p3 = Point(3, 4)
    p4 = Point(0, 4)

    result = calculate_centroid([p1, p2, p3, p4])
    assert result.x == 1.5
    assert result.y == 2.0


def test_calculate_centroid_negative_coords() -> None:
    """Test calculate_centroid with negative coordinates."""
    p1 = Point(-2, -2)
    p2 = Point(2, 2)

    result = calculate_centroid([p1, p2])
    assert result.x == 0.0
    assert result.y == 0.0


if __name__ == "__main__":
    # Run all tests
    # IMPORTANT: Run tests with actual data FIRST so RightTyper can infer proper types
    test_point_creation()
    test_point_distance()
    test_point_equality()

    # Run tests with data before edge cases
    test_find_closest_points_basic()
    test_find_closest_points_multiple_pairs()
    test_find_closest_points_no_matches()
    test_find_closest_points_single()
    test_find_closest_points_empty()  # Edge cases last

    test_calculate_centroid_two_points()
    test_calculate_centroid_multiple_points()
    test_calculate_centroid_negative_coords()
    test_calculate_centroid_single()
    test_calculate_centroid_empty()  # Edge cases last

    print("All tests passed!")
