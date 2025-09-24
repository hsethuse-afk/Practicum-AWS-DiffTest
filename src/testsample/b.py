from typing import List, Tuple, Dict, Set
import math

def optimize_delivery_routes(packages: Dict[str, Tuple[int, int]], 
                           truck_capacity: int, 
                           depot: Tuple[int, int]) -> List[List[str]]:
    """
    Given a dictionary of packages with their coordinates and a truck capacity,
    group packages into optimal delivery routes. Each route should not exceed truck capacity.
    Packages are grouped by proximity to minimize total travel distance.
    
    Args:
    - packages: Dict mapping package_id to (x, y) coordinates  
    - truck_capacity: Maximum packages per route
    - depot: Starting point (x, y) coordinates
    
    Returns: List of routes, where each route is a list of package IDs
    
    Example:
    optimize_delivery_routes(
        {"P1": (1, 1), "P2": (2, 2), "P3": (10, 10), "P4": (11, 11)}, 
        2, 
        (0, 0)
    ) => [["P1", "P2"], ["P3", "P4"]]
    """
    if not packages:
        return []
    
    def distance(p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    # Sort packages by distance from depot
    sorted_packages = sorted(packages.items(), 
                           key=lambda item: distance(depot, item[1]))
    
    routes = []
    current_route = []
    
    for package_id, coords in sorted_packages:
        if len(current_route) < truck_capacity:
            current_route.append(package_id)
        else:
            routes.append(current_route)
            current_route = [package_id]
    
    if current_route:
        routes.append(current_route)
    
    return routes
