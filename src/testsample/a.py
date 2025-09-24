
from typing import List, Tuple, Dict, Set

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
    
    def euclidean_distance(p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
        return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**0.5
    
    remaining_packages = list(packages.keys())
    routes = []
    
    while remaining_packages:
        current_route = []
        current_pos = depot
        
        while len(current_route) < truck_capacity and remaining_packages:
            # Find closest package to current position
            closest_package = min(remaining_packages, 
                                key=lambda p: euclidean_distance(current_pos, packages[p]))
            
            current_route.append(closest_package)
            current_pos = packages[closest_package]
            remaining_packages.remove(closest_package)
        
        routes.append(current_route)
    
    return routes
