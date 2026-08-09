"""Common interface implemented by every pathfinding algorithm."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models.grid import Grid
from ..models.path_result import PathResult
from ..models.point import Point


class BasePathfinder(ABC):
    """Abstract base class for grid pathfinders.

    Every implementation must honour the following contract in
    :meth:`find_path`:

    * Validate inputs: if ``start`` or ``goal`` is out of bounds or on an
      obstacle, return a not-found :class:`PathResult` with an empty path.
    * When ``start == goal`` (and walkable), return a path containing just that
      point.
    * On success, return the reconstructed path from start to goal inclusive.
      Cost-aware planners (A*, Dijkstra) return a path minimising the total
      accumulated cost — step cost plus each entered cell's :meth:`Grid.cost`.
      BFS returns a minimum move-count path and ignores the cost channel; DFS is
      not optimal.
    * When the goal is unreachable, return a not-found result with an empty
      path.
    * Always populate ``visited_nodes`` and ``execution_time_ms``.
    """

    @abstractmethod
    def find_path(self, grid: Grid, start: Point, goal: Point) -> PathResult:
        """Search ``grid`` for a path from ``start`` to ``goal``."""
        raise NotImplementedError

    @abstractmethod
    def name(self) -> str:
        """Return the human-readable name of the algorithm."""
        raise NotImplementedError
