"""Breadth-first search pathfinder."""

from __future__ import annotations

from collections import deque
from time import perf_counter

from ..models.grid import Grid
from ..models.path_result import PathResult
from ..models.point import Point
from .base_pathfinder import BasePathfinder


class BfsPathfinder(BasePathfinder):
    """Breadth-first search on a dynamic, 8-connected grid.

    BFS explores the grid level by level using a FIFO queue, so the first time
    the goal is dequeued it has been reached by a path with the fewest moves.
    Movement follows :meth:`Grid.neighbors` — the four cardinal directions plus
    the diagonals (no corner cutting). Because every move costs the same, the
    returned path minimises the *number of moves* (Chebyshev distance), not the
    Euclidean distance; weighted diagonals would require Dijkstra or A*.

    The search operates on the grid's state at call time, so a map that changes
    as sensor data arrives is handled simply by calling :meth:`find_path` again
    after each update. The grid's size need not be known in advance.
    """

    def name(self) -> str:
        return "BFS"

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

        frontier: deque[Point] = deque((start,))
        came_from: dict[Point, Point | None] = {start: None}
        visited_nodes = 0

        while frontier:
            current = frontier.popleft()
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

            for neighbor in grid.neighbors(current):
                if neighbor not in came_from:
                    came_from[neighbor] = current
                    frontier.append(neighbor)

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
