"""Dynamic 2D occupancy grid with obstacle tracking and neighbour generation."""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from .point import Point

# 4-connected movement, in a fixed order: up, down, left, right.
_CARDINAL: tuple[tuple[int, int], ...] = ((0, -1), (0, 1), (-1, 0), (1, 0))
# Diagonal movement: upper-left, upper-right, bottom-left, bottom-right.
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

    Movement is **8-connected** by default (the four cardinal directions plus the
    four diagonals). Diagonal moves may not *cut corners*: a diagonal step is
    forbidden when either orthogonally-adjacent cell it passes is an obstacle,
    which keeps paths realistic for a robot that has physical width. Pass
    ``allow_diagonal=False`` to restrict movement to 4-connectivity.
    """

    def __init__(
        self,
        width: int,
        height: int,
        obstacles: Iterable[Point] | None = None,
        *,
        allow_diagonal: bool = True,
    ) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("grid width and height must be positive")
        self.width = width
        self.height = height
        self.allow_diagonal = allow_diagonal
        self._obstacles: set[Point] = set(obstacles) if obstacles is not None else set()

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

    def resize(self, width: int, height: int) -> None:
        """Change the grid dimensions, dropping obstacles now out of bounds."""
        if width <= 0 or height <= 0:
            raise ValueError("grid width and height must be positive")
        self.width = width
        self.height = height
        self._obstacles = {p for p in self._obstacles if self.in_bounds(p)}

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
    ) -> None:
        """Apply a sensor update, growing the grid to fit any new points.

        Points in ``occupied`` are marked as obstacles; points in ``free`` are
        cleared. The grid auto-expands via :meth:`ensure_contains` so updates may
        reference cells beyond the current bounds.
        """
        for point in occupied:
            self.ensure_contains(point)
            self._obstacles.add(point)
        for point in free:
            self.ensure_contains(point)
            self._obstacles.discard(point)

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
