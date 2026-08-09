"""Dijkstra search pathfinder."""

from __future__ import annotations

import heapq
from itertools import count
from time import perf_counter

from ..models.grid import Grid
from ..models.path_result import PathResult
from ..models.point import Point
from .base_pathfinder import BasePathfinder

_SQRT2 = 2**0.5


class DijkstraPathfinder(BasePathfinder):
    """Dijkstra search on a grid using a binary-heap priority queue.

    Dijkstra expands nodes in order of accumulated cost ``g(n)`` from the start,
    which is A* with a zero heuristic. With non-negative costs this yields a
    shortest path. Without heuristic guidance it explores by cost layers like
    BFS, so it typically visits more nodes than A*.

    Movement follows :meth:`Grid.neighbors`, so the grid's ``allow_diagonal``
    setting is honoured (including the no-corner-cutting rule). Cardinal steps
    cost ``1.0`` and diagonal steps ``sqrt(2)``, plus the destination cell's
    :meth:`Grid.cost` (a gradient costmap layer, ``0.0`` by default), so paths
    prefer lower-cost cells while remaining able to traverse them when cheaper.
    """

    def name(self) -> str:
        """Return the algorithm's short name (``"Dijkstra"``)."""
        return "Dijkstra"

    def find_path(self, grid: Grid, start: Point, goal: Point) -> PathResult:
        """Find the lowest-cost path from ``start`` to ``goal`` via Dijkstra."""
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
        open_heap: list[tuple[float, int, Point]] = [(0.0, next(counter), start)]
        cost_so_far: dict[Point, float] = {start: 0.0}
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

            for neighbor in grid.neighbors(current):
                new_cost = (
                    cost_so_far[current]
                    + _move_cost(current, neighbor)
                    + grid.cost(neighbor)
                )
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    came_from[neighbor] = current
                    heapq.heappush(open_heap, (new_cost, next(counter), neighbor))

        return PathResult.empty(
            execution_time_ms=_elapsed_ms(start_time),
            visited_nodes=visited_nodes,
        )


def _move_cost(a: Point, b: Point) -> float:
    """Cost of a single step: ``sqrt(2)`` for a diagonal move, ``1.0`` otherwise."""
    return _SQRT2 if (a.x != b.x and a.y != b.y) else 1.0


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
