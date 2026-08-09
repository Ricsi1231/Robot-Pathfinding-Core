"""Dynamic 2D occupancy grid with obstacle tracking and neighbour generation."""

from __future__ import annotations

import math
from collections.abc import Iterable, Iterator, Mapping

from .point import Point

_CARDINAL: tuple[tuple[int, int], ...] = ((0, -1), (0, 1), (-1, 0), (1, 0))
_DIAGONAL: tuple[tuple[int, int], ...] = ((-1, -1), (1, -1), (-1, 1), (1, 1))


class Grid:
    """A dynamic occupancy grid of walkable cells and obstacles.

    The grid spans ``x`` in ``0 .. width - 1`` and ``y`` in ``0 .. height - 1``,
    with cells walkable unless marked as obstacles.

    The size is **not fixed**: a robot typically does not know the map extent in
    advance and builds it up from sensor data. The grid can therefore grow and
    have cells flipped free/occupied at runtime via :meth:`update`,
    :meth:`resize`, and :meth:`ensure_contains`. The grid grows from the origin
    in the ``+x`` / ``+y`` directions only; negative coordinates are not
    supported (a documented limitation).

    A grid may be **empty** (either dimension ``0``, e.g. a map that has not
    received sensor data yet) — see :attr:`is_empty`. An empty grid has no
    walkable cells, so any search over it returns a not-found result, and it can
    grow from the origin via :meth:`update` / :meth:`ensure_contains`. Only
    *negative* dimensions are rejected.

    Movement is **8-connected** by default (the four cardinal directions plus the
    four diagonals). Diagonal moves may not *cut corners*: a diagonal step is
    forbidden when either orthogonally-adjacent cell it passes is an obstacle,
    which keeps paths realistic for a robot that has physical width. Pass
    ``allow_diagonal=False`` to restrict movement to 4-connectivity.

    Separately from the binary walkable/obstacle state, each cell carries an
    optional **traversal cost** (default ``0.0``), a gradient costmap layer that
    lets paths prefer clearance. Weighted planners (A* and Dijkstra) add
    :meth:`cost` to their step cost; BFS and DFS ignore it. See :meth:`set_cost`.
    """

    def __init__(
        self,
        width: int,
        height: int,
        obstacles: Iterable[Point] | None = None,
        *,
        allow_diagonal: bool = True,
        costs: Mapping[Point, float] | None = None,
    ) -> None:
        if width < 0 or height < 0:
            raise ValueError("grid width and height must be non-negative")
        self.width = width
        self.height = height
        self.allow_diagonal = allow_diagonal
        self._obstacles: set[Point] = set(obstacles) if obstacles is not None else set()
        self._costs: dict[Point, float] = {}
        if costs is not None:
            for point, value in costs.items():
                self.set_cost(point, value)

    @property
    def is_empty(self) -> bool:
        """Whether the grid has no cells (either dimension is ``0``).

        An empty grid has no walkable cells, so searches return a not-found
        result; it can still grow via :meth:`update` / :meth:`ensure_contains`.
        """
        return self.width == 0 or self.height == 0

    def in_bounds(self, point: Point) -> bool:
        """Return whether ``point`` lies within the grid boundaries."""
        return 0 <= point.x < self.width and 0 <= point.y < self.height

    def is_obstacle(self, point: Point) -> bool:
        """Return whether ``point`` is marked as an obstacle."""
        return point in self._obstacles

    def is_walkable(self, point: Point) -> bool:
        """Return whether ``point`` is in bounds and not an obstacle."""
        return self.in_bounds(point) and point not in self._obstacles

    def add_obstacle(self, point: Point) -> None:
        """Mark ``point`` as an obstacle."""
        self._obstacles.add(point)

    def remove_obstacle(self, point: Point) -> None:
        """Unmark ``point`` as an obstacle (no-op if it was not one)."""
        self._obstacles.discard(point)

    def cost(self, point: Point) -> float:
        """Return the traversal cost of ``point`` (``0.0`` if none was set)."""
        return self._costs.get(point, 0.0)

    def set_cost(self, point: Point, value: float) -> None:
        """Set the traversal cost of ``point``.

        ``value`` must be a finite, non-negative number; negative, NaN, and
        infinite costs raise ``ValueError`` (a negative or NaN cost would break
        the weighted planners' shortest-path guarantee, and an impassable cell
        should be an obstacle rather than an infinite cost). Setting ``0.0``
        clears any stored cost. Cost on an obstacle cell is inert — the search
        never enters it.
        """
        if not math.isfinite(value) or value < 0:
            raise ValueError("cell cost must be a finite, non-negative number")
        if value == 0.0:
            self._costs.pop(point, None)
        else:
            self._costs[point] = float(value)

    def resize(self, width: int, height: int) -> None:
        """Change the grid dimensions, dropping obstacles/costs now out of bounds."""
        if width < 0 or height < 0:
            raise ValueError("grid width and height must be non-negative")
        self.width = width
        self.height = height
        self._obstacles = {p for p in self._obstacles if self.in_bounds(p)}
        self._costs = {p: c for p, c in self._costs.items() if self.in_bounds(p)}

    def ensure_contains(self, point: Point) -> None:
        """Grow the grid so ``point`` falls within bounds.

        Expands ``width`` / ``height`` as needed (the origin stays at ``(0, 0)``).
        Negative coordinates are unsupported and raise ``ValueError``.
        """
        if point.x < 0 or point.y < 0:
            raise ValueError("grid does not support negative coordinates")
        if point.x >= self.width:
            self.width = point.x + 1
        if point.y >= self.height:
            self.height = point.y + 1

    def update(
        self,
        *,
        occupied: Iterable[Point] = (),
        free: Iterable[Point] = (),
        costs: Mapping[Point, float] | None = None,
    ) -> None:
        """Apply a sensor update, growing the grid to fit any new points.

        Points in ``occupied`` are marked as obstacles; points in ``free`` are
        cleared; ``costs`` maps cells to their new traversal cost. The grid
        auto-expands via :meth:`ensure_contains` so updates may reference cells
        beyond the current bounds. Occupancy and cost are independent channels —
        clearing a cell via ``free`` leaves its cost untouched. All ``costs``
        values are validated before anything is applied, so a batch containing an
        invalid cost is rejected without partially mutating the grid.
        """
        if costs is not None:
            for value in costs.values():
                if not math.isfinite(value) or value < 0:
                    raise ValueError("cell cost must be a finite, non-negative number")
        for point in occupied:
            self.ensure_contains(point)
            self._obstacles.add(point)
        for point in free:
            self.ensure_contains(point)
            self._obstacles.discard(point)
        if costs is not None:
            for point, value in costs.items():
                self.ensure_contains(point)
                self.set_cost(point, value)

    def neighbors(self, point: Point) -> Iterator[Point]:
        """Yield the walkable neighbours of ``point``.

        Cardinal neighbours (up, down, left, right) come first, followed by the
        diagonals when ``allow_diagonal`` is set. All candidates are filtered
        through :meth:`is_walkable`, and diagonal moves are additionally rejected
        if they would cut past an obstacle corner. This is the shared expansion
        primitive reused by every search algorithm.
        """
        for dx, dy in _CARDINAL:
            candidate = Point(point.x + dx, point.y + dy)
            if self.is_walkable(candidate):
                yield candidate

        if not self.allow_diagonal:
            return

        for dx, dy in _DIAGONAL:
            candidate = Point(point.x + dx, point.y + dy)
            if not self.is_walkable(candidate):
                continue
            if self.is_obstacle(Point(point.x + dx, point.y)) or self.is_obstacle(
                Point(point.x, point.y + dy)
            ):
                continue
            yield candidate
