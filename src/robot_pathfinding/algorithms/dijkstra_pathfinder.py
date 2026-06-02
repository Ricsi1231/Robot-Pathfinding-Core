"""Dijkstra search pathfinder."""

from __future__ import annotations

import heapq
from itertools import count
from time import perf_counter

from ..models.grid import Grid
from ..models.path_result import PathResult
from ..models.point import Point
from .base_pathfinder import BasePathfinder

_CARDINAL: tuple[tuple[int, int], ...] = ((0, -1), (0, 1), (-1, 0), (1, 0))


class DijkstraPathfinder(BasePathfinder):
    """Dijkstra search on a grid using a binary-heap priority queue.

    Dijkstra expands nodes in order of accumulated cost ``g(n)`` from the start,
    which is A* with a zero heuristic. With non-negative costs this yields a
    shortest path; the current version uses an equal cost of 1 for every valid
    step. Without heuristic guidance it explores by cost layers like BFS, so it
    typically visits more nodes than A*.

    Movement is restricted to the four cardinal directions, independent of the
    grid's diagonal setting.
    """

    def name(self) -> str:
        return "Dijkstra"

    def find_path(self, grid: Grid, start: Point, goal: Point) -> PathResult:
        start_time = perf_counter()

        if not grid.is_walkable(start) or not grid.is_walkable(goal):
            return PathResult.empty(execution_time_ms=_elapsed_ms(start_time))

        if start == goal:
            return PathResult(
                found=True,
                path=[start],
                visited_nodes=1,
                path_length=1,
                execution_time_ms=_elapsed_ms(start_time),
            )

        counter = count()
        open_heap: list[tuple[int, int, Point]] = [(0, next(counter), start)]
        cost_so_far: dict[Point, int] = {start: 0}
        came_from: dict[Point, Point | None] = {start: None}
        closed: set[Point] = set()
        visited_nodes = 0

        while open_heap:
            _, _, current = heapq.heappop(open_heap)
            if current in closed:
                continue
            closed.add(current)
            visited_nodes += 1

            if current == goal:
                path = _reconstruct_path(came_from, goal)
                return PathResult(
                    found=True,
                    path=path,
                    visited_nodes=visited_nodes,
                    path_length=len(path),
                    execution_time_ms=_elapsed_ms(start_time),
                )

            for dx, dy in _CARDINAL:
                neighbor = Point(current.x + dx, current.y + dy)
                if not grid.is_walkable(neighbor):
                    continue
                new_cost = cost_so_far[current] + 1
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    came_from[neighbor] = current
                    heapq.heappush(open_heap, (new_cost, next(counter), neighbor))

        return PathResult.empty(
            execution_time_ms=_elapsed_ms(start_time),
            visited_nodes=visited_nodes,
        )


def _elapsed_ms(start_time: float) -> float:
    return (perf_counter() - start_time) * 1000.0


def _reconstruct_path(
    came_from: dict[Point, Point | None],
    goal: Point,
) -> list[Point]:
    """Walk predecessors from ``goal`` back to the start, then reverse."""
    path: list[Point] = []
    node: Point | None = goal
    while node is not None:
        path.append(node)
        node = came_from[node]
    path.reverse()
    return path
