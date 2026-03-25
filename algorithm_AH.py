# -*- coding: utf-8 -*-
"""
Implements the 2-opt swap algorithm for solving the
Travelling Salesman Problem (TSP) — finding the shortest
delivery route through a set of locations.
"""

import math
from dataclasses import dataclass, field


# Data model

@dataclass
class Location:
    postcode: str
    latitude: float
    longitude: float
    district: str = ""
    ward: str = ""

    def __repr__(self):
        return f"Location({self.postcode})"


@dataclass
class OptimisationResult:
    route: list
    total_distance_km: float
    iterations: int
    initial_distance_km: float
    distance_matrix: list 
    improvement_log: list[str] = field(default_factory=list)


# Distance

def haversine(a: Location, b: Location) -> float:
    """
    Calculate the great-circle distance between two points on Earth
    using the Haversine formula. Returns distance in kilometres.
    """
    earth_radius = 6371.0  # Earth's mean radius in km

    latitude_1, longitude_1 = math.radians(a.latitude), math.radians(a.longitude)
    latitude_2, longitude_2 = math.radians(b.latitude), math.radians(b.longitude)

    latitude_dist = latitude_2 - latitude_1
    longitude_dist = longitude_2 - longitude_1

    sin_dlat = math.sin(latitude_dist / 2)
    sin_dlng = math.sin(longitude_dist / 2)

    h = (sin_dlat ** 2
         + math.cos(latitude_1) * math.cos(latitude_2) * sin_dlng ** 2)

    return earth_radius * 2 * math.atan2(math.sqrt(h), math.sqrt(1 - h))


def build_distance_matrix(locations: list[Location]) -> list[list[float]]:
    """
    Build a symmetric distance matrix for all locations.
    matrix[i][j] = haversine distance between location i and j.
    """
    n = len(locations)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine(locations[i], locations[j])
            matrix[i][j] = d
            matrix[j][i] = d
    return matrix


def route_distance(route: list[Location], depot: Location,
                   matrix: list[list[float]], all_locs: list[Location]) -> float:
    """
    Calculate total distance for a route (depot to stops back to depot).
    """
    # Map location objects to indices in all_locs
    idx = {id(loc): i for i, loc in enumerate(all_locs)}

    total = 0.0
    prev = depot
    for stop in route:
        total += matrix[idx[id(prev)]][idx[id(stop)]]
        prev = stop
    total += matrix[idx[id(prev)]][idx[id(depot)]] 
    return total


# Nearest Neighbour heuristic

def nearest_neighbour(stops: list[Location], depot: Location,
                      matrix: list[list[float]], all_locs: list[Location]) -> list[Location]:
    """
    Greedy nearest-neighbour heuristic to build an initial route.
    Starting from the depot, always visit the closest unvisited stop next.
    This gives a reasonable starting point for 2-opt to improve upon.
    """
    idx = {id(loc): i for i, loc in enumerate(all_locs)}
    unvisited = list(stops)
    route = []
    current = depot

    while unvisited:
        # Find closest unvisited stop to current location
        nearest = min(unvisited,
                      key=lambda s: matrix[idx[id(current)]][idx[id(s)]])
        route.append(nearest)
        unvisited.remove(nearest)
        current = nearest

    return route


# 2-Opt Swap

def two_opt_swap(route: list[Location], i: int, k: int) -> list[Location]:
    """
    Perform a 2-opt swap by reversing the sub-route between index i and k.
    """
    return route[:i] + route[i:k + 1][::-1] + route[k + 1:]


def two_opt(stops: list[Location], depot: Location,
            matrix: list[list[float]], all_locs: list[Location],
            progress_callback=None) -> OptimisationResult:
    """
    Optimise a delivery route using the 2-opt swap algorithm.
    """
    def log(msg):
        if progress_callback:
            progress_callback(msg)

    # Seed with nearest-neighbour
    route = nearest_neighbour(stops, depot, matrix, all_locs)
    initial_dist = route_distance(route, depot, matrix, all_locs)
    best_dist = initial_dist

    log(f"Nearest-neighbour seed: {initial_dist:.2f} km")

    improvement_log = [f"Initial (nearest-neighbour): {initial_dist:.2f} km"]
    iterations = 0
    improved = True

    # Iterative 2-opt improvement
    while improved:
        improved = False
        iterations += 1
        n = len(route)

        for i in range(1, n - 1):
            for k in range(i + 1, n):
                candidate = two_opt_swap(route, i, k)
                candidate_dist = route_distance(candidate, depot, matrix, all_locs)

                if candidate_dist < best_dist - 1e-6:
                    route = candidate
                    best_dist = candidate_dist
                    improved = True
                    improvement_log.append(
                        f"Iteration {iterations}, swap({i},{k}): {best_dist:.2f} km"
                    )

    log(f"2-opt complete. {iterations} iteration(s). Final: {best_dist:.2f} km")
    log(f"Improvement: {initial_dist - best_dist:.2f} km saved "
        f"({(initial_dist - best_dist) / initial_dist * 100:.1f}%)")

    return OptimisationResult(
        route=route,
        total_distance_km=best_dist,
        iterations=iterations,
        initial_distance_km=initial_dist,
        distance_matrix=matrix,
        improvement_log=improvement_log,
    )


# Public helper

def optimise_route(depot: Location, stops: list[Location],
                   progress_callback=None) -> OptimisationResult:
    """
    Given a depot and list of stops, return the
    optimised route using nearest-neighbour + 2-opt.
    """
    all_locs = [depot] + stops
    matrix = build_distance_matrix(all_locs)
    return two_opt(stops, depot, matrix, all_locs, progress_callback)