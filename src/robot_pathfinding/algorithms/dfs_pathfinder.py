"""Depth-first search pathfinder."""

from __future__ import annotations

from time import perf_counter

from ..models.grid import Grid
from ..models.path_result import PathResult
from ..models.point import Point
from .base_pathfinder import BasePathfinder

_CARDINAL: tuple[tuple[int, int], ...] = ((0, -1), (0, 1), (-1, 0), (1, 0))


class DfsPathfinder(BasePathfinder):
    """Depth-first search on a grid using an explicit LIFO stack.

    DFS explores as deep as possible along each branch before backtracking. It
    is implemented iteratively (with a stack rather than recursion) to avoid
    recursion-depth limits on large maps. Movement is restricted to the four
    cardinal directions, independent of the grid's diagonal setting.

    Unlike BFS, DFS does **not** guarantee a shortest path; it returns the first
    valid path it discovers. Its purpose here is educational comparison against
    BFS, Greedy, Dijkstra, and A*.
    """

    def name(self) -> str:
        return "DFS"

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

        stack: list[Point] = [start]
        came_from: dict[Point, Point | None] = {start: None}
        visited_nodes = 0

        while stack:
            current = stack.pop()
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
                if grid.is_walkable(neighbor) and neighbor not in came_from:
                    came_from[neighbor] = current
                    stack.append(neighbor)

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
