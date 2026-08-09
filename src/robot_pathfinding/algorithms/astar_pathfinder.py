"""A* search pathfinder."""

from __future__ import annotations

import heapq
from itertools import count
from time import perf_counter

from ..models.grid import Grid
from ..models.path_result import PathResult
from ..models.point import Point
from .base_pathfinder import BasePathfinder

_SQRT2 = 2**0.5


class AStarPathfinder(BasePathfinder):
    """A* search on a grid using a binary-heap priority queue.

    A* expands nodes in order of ``f(n) = g(n) + h(n)``, where ``g`` is the cost
    from the start and ``h`` is an admissible heuristic. With an admissible
    heuristic this yields an optimal path while expanding fewer nodes than an
    uninformed search such as BFS.

    Movement follows :meth:`Grid.neighbors`, so the grid's ``allow_diagonal``
    setting is honoured (including the no-corner-cutting rule). Cardinal steps
    cost ``1.0`` and diagonal steps ``sqrt(2)``, plus the destination cell's
    :meth:`Grid.cost` (a gradient costmap layer, ``0.0`` by default), so paths
    prefer lower-cost cells while remaining able to traverse them when cheaper.
    The heuristic is octile when diagonals are allowed and Manhattan otherwise;
    both stay admissible and consistent because per-cell costs are non-negative.
    """

    def name(self) -> str:
        """Return the algorithm's short name (``"A*"``)."""
        return "A*"

    def find_path(self, grid: Grid, start: Point, goal: Point) -> PathResult:
        """Find the lowest-cost path from ``start`` to ``goal`` via A* search."""
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
        open_heap: list[tuple[float, int, Point]] = [
            (
                _heuristic(start, goal, allow_diagonal=grid.allow_diagonal),
                next(counter),
                start,
            )
        ]
        came_from: dict[Point, Point | None] = {start: None}
        g_score: dict[Point, float] = {start: 0.0}
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

            for neighbor in grid.neighbors(current):
                tentative_g = (
                    g_score[current]
                    + _move_cost(current, neighbor)
                    + grid.cost(neighbor)
                )
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    g_score[neighbor] = tentative_g
                    came_from[neighbor] = current
                    h = _heuristic(neighbor, goal, allow_diagonal=grid.allow_diagonal)
                    heapq.heappush(
                        open_heap, (tentative_g + h, next(counter), neighbor)
                    )

        return PathResult.empty(
            execution_time_ms=_elapsed_ms(start_time),
            visited_nodes=visited_nodes,
        )


def _move_cost(a: Point, b: Point) -> float:
    """Cost of a single step: ``sqrt(2)`` for a diagonal move, ``1.0`` otherwise."""
    return _SQRT2 if (a.x != b.x and a.y != b.y) else 1.0


def _heuristic(a: Point, b: Point, *, allow_diagonal: bool) -> float:
    """Admissible heuristic for the grid's connectivity.

    Octile distance when diagonals are allowed (tight for cardinal cost ``1.0``
    and diagonal cost ``sqrt(2)``); Manhattan distance otherwise.
    """
    dx, dy = abs(a.x - b.x), abs(a.y - b.y)
    if allow_diagonal:
        return (dx + dy) + (_SQRT2 - 2) * min(dx, dy)
    return float(dx + dy)


def _elapsed_ms(start_time: float) -> float:
    """Return milliseconds elapsed since ``start_time``."""
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
