"""A* search pathfinder."""

from __future__ import annotations

import heapq
from itertools import count
from time import perf_counter

from ..models.grid import Grid
from ..models.path_result import PathResult
from ..models.point import Point
from .base_pathfinder import BasePathfinder

_CARDINAL: tuple[tuple[int, int], ...] = ((0, -1), (0, 1), (-1, 0), (1, 0))


class AStarPathfinder(BasePathfinder):
    """A* search on a grid using a binary-heap priority queue.

    A* expands nodes in order of ``f(n) = g(n) + h(n)``, where ``g`` is the cost
    from the start and ``h`` is the Manhattan-distance heuristic. With uniform
    move cost and an admissible heuristic this yields an optimal path while
    expanding fewer nodes than an uninformed search such as BFS.

    Movement is restricted to the four cardinal directions, for which the
    Manhattan heuristic is admissible, independent of the grid's diagonal
    setting.
    """

    def name(self) -> str:
        return "A*"

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
        open_heap: list[tuple[int, int, Point]] = [
            (_heuristic(start, goal), next(counter), start)
        ]
        came_from: dict[Point, Point | None] = {start: None}
        g_score: dict[Point, int] = {start: 0}
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
                tentative_g = g_score[current] + 1
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    g_score[neighbor] = tentative_g
                    came_from[neighbor] = current
                    f_score = tentative_g + _heuristic(neighbor, goal)
                    heapq.heappush(open_heap, (f_score, next(counter), neighbor))

        return PathResult.empty(
            execution_time_ms=_elapsed_ms(start_time),
            visited_nodes=visited_nodes,
        )


def _heuristic(a: Point, b: Point) -> int:
    """Manhattan distance, admissible for 4-direction uniform-cost movement."""
    return abs(a.x - b.x) + abs(a.y - b.y)


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
